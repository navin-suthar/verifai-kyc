"""Local MOCK KYC verification providers.

These endpoints simulate government / bureau checks. Nothing is sent off-box
and no real registry is contacted. Responses are deterministic so demos replay.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from app.core.config import Settings
from app.models.enums import DocumentType, VerificationStatus
from app.services.document_service import doc_type_label, field_value

PROVIDERS = {
    DocumentType.SYNTHETIC_PAN: "MockPANRegistry",
    DocumentType.SYNTHETIC_NATIONAL_ID: "MockNationalIDService",
    DocumentType.SYNTHETIC_PASSPORT: "MockPassportAuthority",
    DocumentType.SYNTHETIC_UTILITY_BILL: "MockUtilityProvider",
    DocumentType.UNKNOWN: "MockDocumentBureau",
}

FAIL_TOKENS = ("FAIL", "0000", "MISSING", "UNKNOWN")
MISMATCH_TOKENS = ("MISMATCH", "PARTIAL", "DIFF")


def provider_for(document_type: DocumentType | str) -> str:
    if isinstance(document_type, str):
        try:
            document_type = DocumentType(document_type)
        except ValueError:
            document_type = DocumentType.UNKNOWN
    return PROVIDERS.get(document_type, PROVIDERS[DocumentType.UNKNOWN])


def _score_bucket(document_number: str, seed: int) -> int:
    digest = hashlib.sha256(f"{seed}:{document_number.upper()}".encode()).hexdigest()
    return int(digest[:8], 16) % 10


def verify_synthetic(
    *,
    name: str | None,
    document_number: str | None,
    document_type: DocumentType,
    date_of_birth: str | None = None,
    address: str | None = None,
    settings: Settings | None = None,
) -> dict:
    """Return a mock registry response. Always labelled as mock."""
    seed = settings.mock_verification_seed if settings else 42
    now = datetime.now(UTC)
    provider = provider_for(document_type)
    number = (document_number or "").strip().upper()
    applicant = (name or "").strip()

    if not number:
        status, score, message = (
            VerificationStatus.ERROR,
            0,
            "Mock registry call skipped: no document number was extracted.",
        )
    elif any(token in number for token in FAIL_TOKENS) or applicant.upper() in {"", "UNKNOWN"}:
        status, score, message = (
            VerificationStatus.NOT_FOUND,
            18 + _score_bucket(number or "NONE", seed),
            "No record found for the supplied identifier (mock).",
        )
    elif any(token in number for token in MISMATCH_TOKENS) or (address and "incomplete" in address.lower()):
        status, score, message = (
            VerificationStatus.MISMATCH,
            68 + _score_bucket(number, seed) % 16,
            "Partial match: name matched, address or date of birth differs (mock).",
        )
    else:
        status, score, message = (
            VerificationStatus.VERIFIED,
            92 + _score_bucket(number, seed) % 8,
            "Synthetic document successfully matched",
        )

    return {
        "provider": provider,
        "status": status.value,
        "match_score": float(score),
        "matchScore": int(score),
        "message": message,
        "is_mock": True,
        "isMock": True,
        "checked_at": now,
        "raw_response": {
            "status": status.value,
            "matchScore": int(score),
            "message": message,
            "provider": provider,
            "mock": True,
            "documentType": doc_type_label(document_type),
            "dateOfBirthChecked": bool(date_of_birth),
        },
    }


def verify_from_fields(fields: list[dict], document_type: DocumentType, settings: Settings) -> dict:
    return verify_synthetic(
        name=field_value(fields, "full_name"),
        document_number=field_value(fields, "document_number"),
        document_type=document_type,
        date_of_birth=field_value(fields, "date_of_birth"),
        address=field_value(fields, "address"),
        settings=settings,
    )
