from __future__ import annotations

import re
from datetime import date

from app.models.enums import DocumentType, Severity
from app.services.document_service import (
    REAL_AADHAAR,
    REAL_PAN,
    SYNTHETIC_NATIONAL,
    SYNTHETIC_PAN,
    SYNTHETIC_PASSPORT,
    SYNTHETIC_UTILITY,
    field_value,
    parse_dob,
)

FORMAT_BY_TYPE = {
    DocumentType.SYNTHETIC_PAN: (SYNTHETIC_PAN, "SYNTHETIC + 4 digits (e.g. SYNTHETIC1234)"),
    DocumentType.SYNTHETIC_NATIONAL_ID: (SYNTHETIC_NATIONAL, "DEMO-####-####-####"),
    DocumentType.SYNTHETIC_PASSPORT: (SYNTHETIC_PASSPORT, "SYNP + 7 digits"),
    DocumentType.SYNTHETIC_UTILITY_BILL: (SYNTHETIC_UTILITY, "ACC-DEMO-######"),
}

ANY_SYNTHETIC = (SYNTHETIC_PAN, SYNTHETIC_NATIONAL, SYNTHETIC_PASSPORT, SYNTHETIC_UTILITY)
POSTAL_RE = re.compile(r"\b\d{5,6}\b")
NAME_OK = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,79}$")


def _check(rule_id: str, name: str, passed: bool, message: str, severity: Severity = Severity.ERROR) -> dict:
    return {
        "rule_id": rule_id,
        "name": name,
        "passed": passed,
        "severity": severity.value,
        "message": message,
    }


def validate_fields(fields: list[dict], document_type: DocumentType) -> list[dict]:
    name = field_value(fields, "full_name")
    dob_raw = field_value(fields, "date_of_birth")
    number = field_value(fields, "document_number")
    address = field_value(fields, "address")
    dob = parse_dob(dob_raw)

    mandatory_ok = all([name, dob_raw, number])
    checks = [
        _check(
            "REQ-001",
            "Mandatory fields present",
            mandatory_ok,
            "Name, date of birth and document number were all extracted."
            if mandatory_ok
            else "One or more mandatory fields (name, date of birth, document number) are missing.",
        )
    ]

    if name:
        name_ok = bool(NAME_OK.match(name)) and len(name.split()) >= 2
        checks.append(
            _check(
                "NAME-001",
                "Applicant name format",
                name_ok,
                "Applicant name looks complete." if name_ok else "Applicant name is incomplete or contains unexpected characters.",
                Severity.WARNING if name else Severity.ERROR,
            )
        )
    else:
        checks.append(_check("NAME-001", "Applicant name format", False, "Applicant name was not extracted."))

    age_ok = False
    age_msg = "Date of birth could not be parsed."
    if dob:
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if dob > today:
            age_msg = "Date of birth is in the future."
        elif age < 18:
            age_msg = f"Applicant appears to be {age} years old (must be 18+)."
        else:
            age_ok = True
            age_msg = f"Applicant is an adult ({age} years) according to the extracted date of birth."
    checks.append(_check("DOB-001", "Applicant age ≥ 18", age_ok, age_msg))

    format_ok = False
    if number:
        expected = FORMAT_BY_TYPE.get(document_type)
        if expected:
            pattern, label = expected
            format_ok = bool(pattern.search(number))
            format_msg = (
                f"Document number matches the synthetic {label} format."
                if format_ok
                else f"Document number does not match the expected synthetic format ({label})."
            )
        else:
            format_ok = any(p.search(number) for p in ANY_SYNTHETIC)
            format_msg = (
                "Document number matches a known synthetic format."
                if format_ok
                else "Document number does not match any supported synthetic format."
            )
    else:
        format_msg = "Document number was not extracted."
    checks.append(_check("FMT-001", "Document number format", format_ok, format_msg))

    haystack = " ".join(v for v in (name, dob_raw, number, address) if v)
    real_pan = bool(REAL_PAN.search(haystack))
    real_aadhaar = bool(REAL_AADHAAR.search(SYNTHETIC_NATIONAL.sub("", haystack)))
    pii_ok = not real_pan and not real_aadhaar
    checks.append(
        _check(
            "PII-001",
            "No real-format identifiers",
            pii_ok,
            "No real-world PAN/Aadhaar patterns detected (privacy guard)."
            if pii_ok
            else "A real-world identity pattern was detected. Real documents are not permitted.",
        )
    )

    if address:
        address_ok = len(address) >= 12 and bool(POSTAL_RE.search(address))
        checks.append(
            _check(
                "ADDR-001",
                "Address completeness",
                address_ok,
                "Address contains a street/locality and a postal code."
                if address_ok
                else "Address is missing a postal code or is too short; manual confirmation needed.",
                Severity.WARNING,
            )
        )
    else:
        checks.append(
            _check(
                "ADDR-001",
                "Address completeness",
                False,
                "Address was not extracted.",
                Severity.WARNING,
            )
        )

    type_ok = document_type != DocumentType.UNKNOWN
    checks.append(
        _check(
            "TYPE-001",
            "Recognised document type",
            type_ok,
            "Document type was classified as a supported synthetic KYC document."
            if type_ok
            else "Document type could not be classified. A reviewer should confirm the document class.",
            Severity.WARNING if type_ok is False else Severity.ERROR,
        )
    )

    return checks


def failed_checks(validation: list[dict], *, severity: str | None = None) -> list[dict]:
    return [
        c
        for c in validation
        if not c.get("passed") and (severity is None or c.get("severity") == severity)
    ]


def issues_from(validation: list[dict]) -> list[str]:
    return [str(c["message"]) for c in validation if not c.get("passed")]
