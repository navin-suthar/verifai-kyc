"""Seed the database with synthetic KYC applications.

All names, identifiers and addresses are invented. Synthetic ID formats are
deliberately different from any real-world scheme:
  - Synthetic PAN      : SYNTHETIC + 4 digits          (e.g. SYNTHETIC1234)
  - Synthetic National : DEMO-####-####-####
  - Synthetic Passport : SYNP + 7 digits
Run:  python -m app.database.seed [--reset]
"""

from __future__ import annotations

import argparse
import hashlib
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models import (
    Application,
    ApplicationStatus,
    AuditAction,
    AuditLog,
    Document,
    DocumentType,
    Review,
    ReviewDecision,
    VerificationResult,
    VerificationStatus,
)
from app.services import audit_service

SYNTHETIC_PEOPLE = [
    ("Rahul Sharma", "1989-04-12", "14 Lotus Lane, Demo Nagar, Mumbai 400001"),
    ("Priya Nair", "1992-11-03", "7 Palm Grove, Sample Town, Kochi 682001"),
    ("Aarav Mehta", "1985-07-28", "221 Example Street, Mock City, Ahmedabad 380001"),
    ("Ananya Iyer", "1996-02-17", "3 Jasmine Court, Demo Colony, Chennai 600001"),
    ("Vikram Rao", "1978-09-09", "88 Placeholder Road, Test Vihar, Hyderabad 500001"),
    ("Sneha Kulkarni", "1990-12-21", "5 Fictional Avenue, Sample Park, Pune 411001"),
    ("Karan Malhotra", "1983-05-30", "19 Dummy Drive, Demo Enclave, New Delhi 110001"),
    ("Isha Banerjee", "1994-08-14", "42 Imaginary Lane, Mock Gardens, Kolkata 700001"),
    ("Rohan Desai", "1987-01-25", "66 Specimen Street, Test Nagar, Surat 395001"),
    ("Meera Pillai", "1991-06-06", "11 Prototype Road, Demo Hills, Bengaluru 560001"),
    ("Arjun Reddy", "1982-03-19", "9 Example Crescent, Sample City, Vijayawada 520001"),
    ("Divya Menon", "1995-10-11", "30 Placeholder Park, Mock Town, Thrissur 680001"),
    ("Nikhil Verma", "1988-12-02", "77 Sandbox Street, Demo Heights, Lucknow 226001"),
    ("Kavya Joshi", "1993-04-23", "2 Stub Lane, Test Colony, Jaipur 302001"),
    ("Aditya Singh", "1980-08-08", "15 Fixture Road, Sample Nagar, Patna 800001"),
    ("Pooja Bhatt", "1997-01-30", "23 Mockup Avenue, Demo Park, Indore 452001"),
    ("Siddharth Kapoor", "1986-05-15", "8 Dummy Court, Example Vihar, Chandigarh 160001"),
    ("Riya Chatterjee", "1990-09-27", "51 Demo Boulevard, Sample Hills, Guwahati 781001"),
]

DOC_TYPES = [
    DocumentType.SYNTHETIC_PAN,
    DocumentType.SYNTHETIC_NATIONAL_ID,
    DocumentType.SYNTHETIC_PASSPORT,
    DocumentType.SYNTHETIC_UTILITY_BILL,
]

# Deterministic scenario mix so the dashboard tells a story.
SCENARIOS = [
    "verified",
    "verified",
    "verified",
    "needs_review",
    "verified",
    "rejected",
    "verified",
    "needs_review",
    "verified",
]


def make_document_number(doc_type: DocumentType, i: int) -> str:
    rnd = random.Random(1000 + i)  # noqa: S311 - deterministic demo data, not security
    if doc_type == DocumentType.SYNTHETIC_PAN:
        return f"SYNTHETIC{rnd.randint(1000, 9999)}"
    if doc_type == DocumentType.SYNTHETIC_NATIONAL_ID:
        return f"DEMO-{rnd.randint(1000, 9999)}-{rnd.randint(1000, 9999)}-{rnd.randint(1000, 9999)}"
    if doc_type == DocumentType.SYNTHETIC_PASSPORT:
        return f"SYNP{rnd.randint(1000000, 9999999)}"
    return f"ACC-DEMO-{rnd.randint(100000, 999999)}"


def mask(number: str) -> str:
    if len(number) <= 4:
        return "••••"
    return f"{number[:4]}{'•' * (len(number) - 8)}{number[-4:]}" if len(number) > 8 else f"••••{number[-4:]}"


def number_hash(number: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{number}".encode()).hexdigest()


def doc_label(doc_type: DocumentType) -> str:
    return {
        DocumentType.SYNTHETIC_PAN: "Synthetic PAN",
        DocumentType.SYNTHETIC_NATIONAL_ID: "Synthetic National ID",
        DocumentType.SYNTHETIC_PASSPORT: "Synthetic Passport",
        DocumentType.SYNTHETIC_UTILITY_BILL: "Synthetic Utility Bill",
    }.get(doc_type, "Unknown")


def build_fields(
    name: str, dob: str, number: str, address: str, doc_type: DocumentType, scenario: str, rnd: random.Random
):
    def conf(base: int) -> float:
        jitter = rnd.randint(-4, 3)
        if scenario == "needs_review":
            jitter -= 12
        elif scenario == "rejected":
            jitter -= 30
        return float(max(35, min(99, base + jitter)))

    return [
        {"name": "full_name", "label": "Full name", "value": name, "confidence": conf(97), "source": "rule"},
        {"name": "date_of_birth", "label": "Date of birth", "value": dob, "confidence": conf(95), "source": "rule"},
        {
            "name": "document_type",
            "label": "Document type",
            "value": doc_label(doc_type),
            "confidence": conf(99),
            "source": "rule",
        },
        {
            "name": "document_number",
            "label": "Document number",
            "value": number,
            "confidence": conf(94),
            "source": "rule",
        },
        {"name": "address", "label": "Address", "value": address, "confidence": conf(90), "source": "rule"},
    ]


def build_validation(scenario: str, doc_type: DocumentType):
    checks = [
        {
            "rule_id": "FMT-001",
            "name": "Document number format",
            "passed": True,
            "severity": "error",
            "message": f"{doc_label(doc_type)} number matches the synthetic format.",
        },
        {
            "rule_id": "DOB-001",
            "name": "Applicant age ≥ 18",
            "passed": True,
            "severity": "error",
            "message": "Applicant is an adult according to the extracted date of birth.",
        },
        {
            "rule_id": "REQ-001",
            "name": "Mandatory fields present",
            "passed": True,
            "severity": "error",
            "message": "Name, date of birth and document number were all extracted.",
        },
        {
            "rule_id": "PII-001",
            "name": "No real-format identifiers",
            "passed": True,
            "severity": "error",
            "message": "No real-world PAN/Aadhaar patterns detected (privacy guard).",
        },
        {
            "rule_id": "ADDR-001",
            "name": "Address completeness",
            "passed": True,
            "severity": "warning",
            "message": "Address contains street, locality and postal code.",
        },
    ]
    if scenario == "needs_review":
        checks[4] = {
            **checks[4],
            "passed": False,
            "message": "Address is missing a postal code; manual confirmation needed.",
        }
    if scenario == "rejected":
        checks[0] = {
            **checks[0],
            "passed": False,
            "message": "Document number does not match the expected synthetic pattern.",
        }
        checks[1] = {**checks[1], "passed": False, "message": "Date of birth could not be parsed reliably."}
    return checks


def build_verification(scenario: str, doc_type: DocumentType, rnd: random.Random, when: datetime) -> VerificationResult:
    provider = {
        DocumentType.SYNTHETIC_PAN: "MockPANRegistry",
        DocumentType.SYNTHETIC_NATIONAL_ID: "MockNationalIDService",
        DocumentType.SYNTHETIC_PASSPORT: "MockPassportAuthority",
        DocumentType.SYNTHETIC_UTILITY_BILL: "MockUtilityProvider",
    }[doc_type]
    if scenario == "verified":
        status, score, msg = VerificationStatus.VERIFIED, rnd.randint(92, 99), "Synthetic document successfully matched"
    elif scenario == "needs_review":
        status, score, msg = (
            VerificationStatus.MISMATCH,
            rnd.randint(68, 84),
            "Partial match: name matched, address differs",
        )
    else:
        status, score, msg = (
            VerificationStatus.NOT_FOUND,
            rnd.randint(10, 40),
            "No record found for the supplied identifier",
        )
    return VerificationResult(
        provider=provider,
        status=status,
        match_score=float(score),
        message=msg,
        is_mock=True,
        raw_response={"status": status.value, "matchScore": score, "message": msg, "mock": True},
        checked_at=when,
    )


def explanation_for(scenario: str, name: str, doc_type: DocumentType) -> str:
    if scenario == "verified":
        return (
            f"All mandatory fields were extracted with high confidence and every validation rule passed. "
            f"The mock {doc_label(doc_type)} registry returned a strong match for {name}, so the application "
            f"was verified automatically."
        )
    if scenario == "needs_review":
        return (
            "Extraction confidence fell into the review band and the address completeness check failed. "
            "The mock registry reported only a partial match, so the application was routed to a human reviewer."
        )
    return (
        "The document number did not match the expected synthetic format and the date of birth could not be "
        "parsed. The mock registry found no matching record. The application was rejected pending investigation."
    )


def seed(db: Session, *, reset: bool = False) -> int:
    settings = get_settings()
    if reset:
        for table in (Review, VerificationResult, Document, Application, AuditLog):
            db.execute(delete(table))
        db.commit()

    if db.query(Application).count() > 0:
        return 0

    now = datetime.now(UTC)
    created = 0
    for i, (name, dob, address) in enumerate(SYNTHETIC_PEOPLE):
        rnd = random.Random(i)  # noqa: S311
        scenario = SCENARIOS[i % len(SCENARIOS)]
        doc_type = DOC_TYPES[i % len(DOC_TYPES)]
        number = make_document_number(doc_type, i)
        created_at = now - timedelta(days=i % 13, hours=rnd.randint(0, 9), minutes=rnd.randint(0, 59))

        fields = build_fields(name, dob, number, address, doc_type, scenario, rnd)
        confidence = round(sum(f["confidence"] for f in fields) / len(fields), 1)
        validation = build_validation(scenario, doc_type)
        issues = [c["message"] for c in validation if not c["passed"]]

        status = {
            "verified": ApplicationStatus.VERIFIED,
            "needs_review": ApplicationStatus.NEEDS_REVIEW,
            "rejected": ApplicationStatus.REJECTED,
        }[scenario]

        app = Application(
            customer_id=f"DEMO-{10001 + i}",
            applicant_name=name,
            document_type=doc_type,
            document_number_masked=mask(number),
            document_number_hash=number_hash(number, settings.secret_key),
            status=status,
            confidence=confidence,
            decision_reason={
                "verified": (
                    f"Confidence {confidence:.0f}% ≥ {settings.auto_verify_min_confidence}% and all checks passed."
                ),
                "needs_review": (
                    f"Confidence {confidence:.0f}% within review band "
                    f"[{settings.review_min_confidence}%, {settings.auto_verify_min_confidence}%)."
                ),
                "rejected": (
                    f"Confidence {confidence:.0f}% < {settings.review_min_confidence}% with failed mandatory checks."
                ),
            }[scenario],
            explanation=explanation_for(scenario, name, doc_type),
            fields=fields,
            validation=validation,
            issues=issues,
            thresholds={
                "auto_verify_min": settings.auto_verify_min_confidence,
                "review_min": settings.review_min_confidence,
            },
            created_at=created_at,
            updated_at=created_at + timedelta(minutes=2),
        )

        text = (
            f"{doc_label(doc_type).upper()} (SYNTHETIC - FOR DEMO ONLY)\n"
            f"Name: {name}\nDate of Birth: {dob}\nDocument Number: {number}\nAddress: {address}\n"
        )
        app.document = Document(
            filename=f"{name.lower().replace(' ', '_')}_{doc_type.value}.txt",
            mime_type="text/plain",
            size_bytes=len(text.encode()),
            sha256=hashlib.sha256(text.encode()).hexdigest(),
            storage_path=None,
            extracted_text=text,
            page_count=1,
        )
        app.verification = build_verification(scenario, doc_type, rnd, created_at + timedelta(minutes=1))

        # A few reviewed items so the review history is populated.
        if scenario == "needs_review" and i % 2 == 1:
            app.reviews.append(
                Review(
                    decision=ReviewDecision.APPROVE,
                    reviewer=settings.demo_username,
                    notes="Address confirmed against supplementary synthetic utility bill.",
                    created_at=created_at + timedelta(hours=3),
                )
            )
            app.status = ApplicationStatus.VERIFIED

        db.add(app)
        db.flush()

        for action in (
            AuditAction.DOCUMENT_UPLOADED,
            AuditAction.EXTRACTION_COMPLETED,
            AuditAction.VALIDATION_COMPLETED,
            AuditAction.VERIFICATION_COMPLETED,
            AuditAction.DECISION_MADE,
        ):
            entry = audit_service.record(
                db,
                action=action,
                entity_type="application",
                entity_id=app.id,
                actor="pipeline",
                details={"customer_id": app.customer_id, "status": app.status.value, "seeded": True},
            )
            entry.timestamp = created_at + timedelta(seconds=10 * list(AuditAction).index(action))
        created += 1

    db.commit()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic KYC demo data")
    parser.add_argument("--reset", action="store_true", help="Delete existing rows before seeding")
    args = parser.parse_args()

    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        n = seed(db, reset=args.reset)
    print(f"Seeded {n} synthetic applications" if n else "Database already contains data; nothing seeded")


if __name__ == "__main__":
    main()
