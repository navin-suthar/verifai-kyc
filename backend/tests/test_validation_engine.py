from app.models.enums import ApplicationStatus, DocumentType
from app.services.decision_service import decide_status
from app.services.document_service import (
    DocumentError,
    contains_real_identity_pattern,
    extract_fields_from_text,
    extract_fields_from_json,
    sanitize_filename,
)
from app.services.validation_service import validate_fields


def test_privacy_guard_rejects_real_pan_and_aadhaar_shapes() -> None:
    assert contains_real_identity_pattern("PAN ABCDE1234F") is not None
    assert contains_real_identity_pattern("ID 1234 5678 9012") is not None
    assert contains_real_identity_pattern("SYNTHETIC1234") is None
    assert contains_real_identity_pattern("DEMO-1234-5678-9012") is None


def test_filename_is_sanitised() -> None:
    assert ".." not in sanitize_filename("../etc/passwd")
    assert "/" not in sanitize_filename("a/b\\c.txt")
    assert sanitize_filename("Rahul Sharma PAN.txt").endswith(".txt")


def test_text_extraction_synthetic_pan() -> None:
    text = "Name: Rahul Sharma\nDate of Birth: 1989-04-12\nPAN: SYNTHETIC1234\nAddress: 14 Lotus Lane, Demo Nagar, Mumbai 400001\n"
    fields, doc_type = extract_fields_from_text(text)
    assert doc_type == DocumentType.SYNTHETIC_PAN
    values = {f["name"]: f["value"] for f in fields}
    assert values["full_name"] == "Rahul Sharma"
    assert values["document_number"] == "SYNTHETIC1234"
    assert values["date_of_birth"] == "1989-04-12"


def test_json_extraction() -> None:
    fields, doc_type = extract_fields_from_json(
        {
            "name": "Priya Nair",
            "dateOfBirth": "1992-11-03",
            "documentNumber": "DEMO-4821-9033-1170",
            "address": "7 Palm Grove, Sample Town, Kochi 682001",
            "documentType": "synthetic_national_id",
        }
    )
    assert doc_type == DocumentType.SYNTHETIC_NATIONAL_ID
    assert any(f["name"] == "full_name" and f["value"] == "Priya Nair" for f in fields)


def test_validation_passes_complete_synthetic_record() -> None:
    fields, doc_type = extract_fields_from_text(
        "Name: Rahul Sharma\nDate of Birth: 1989-04-12\nDocument Number: SYNTHETIC1234\n"
        "Address: 14 Lotus Lane, Demo Nagar, Mumbai 400001\nDocument Type: Synthetic PAN\n"
    )
    checks = validate_fields(fields, doc_type)
    assert all(c["passed"] for c in checks if c["rule_id"] != "ADDR-001" or c["passed"])
    assert all(c["passed"] for c in checks if c["severity"] == "error")


def test_validation_fails_underage_and_bad_format() -> None:
    fields, doc_type = extract_fields_from_text(
        "Name: Test User\nDate of Birth: 2015-01-01\nDocument Number: FAIL0000\nAddress: n/a\n"
    )
    checks = {c["rule_id"]: c for c in validate_fields(fields, doc_type)}
    assert checks["DOB-001"]["passed"] is False
    assert checks["FMT-001"]["passed"] is False


def test_decision_thresholds() -> None:
    ok = [{"rule_id": "REQ-001", "passed": True, "severity": "error", "name": "x", "message": "ok"}]
    verified, _ = decide_status(
        confidence=94,
        validation=ok,
        verification={"status": "verified"},
        auto_verify_min=90,
        review_min=70,
    )
    assert verified == ApplicationStatus.VERIFIED

    review, _ = decide_status(
        confidence=80,
        validation=ok,
        verification={"status": "verified"},
        auto_verify_min=90,
        review_min=70,
    )
    assert review == ApplicationStatus.NEEDS_REVIEW

    rejected, _ = decide_status(
        confidence=55,
        validation=ok,
        verification={"status": "not_found"},
        auto_verify_min=90,
        review_min=70,
    )
    assert rejected == ApplicationStatus.REJECTED


def test_error_rule_blocks_auto_verify_even_at_high_confidence() -> None:
    failed = [{"rule_id": "REQ-001", "passed": False, "severity": "error", "name": "x", "message": "missing"}]
    status, reason = decide_status(
        confidence=96,
        validation=failed,
        verification={"status": "verified"},
        auto_verify_min=90,
        review_min=70,
    )
    assert status == ApplicationStatus.NEEDS_REVIEW
    assert "Mandatory" in reason or "REQ-001" in reason


def test_extract_rejects_empty() -> None:
    from app.core.config import get_settings
    from app.services.document_service import extract

    try:
        extract(b"", "x.txt", "text/plain", get_settings())
        raise AssertionError("expected DocumentError")
    except DocumentError:
        pass
