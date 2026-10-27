from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SettingsDep, UserDep
from app.models.enums import DocumentType
from app.schemas.verify import MockVerifyRequest, MockVerifyResponse
from app.services.verification_service import verify_synthetic

router = APIRouter(prefix="/verify", tags=["mock-verification"])


def _respond(payload: MockVerifyRequest, document_type: DocumentType, settings: SettingsDep) -> MockVerifyResponse:
    result = verify_synthetic(
        name=payload.name,
        document_number=payload.document_number,
        document_type=document_type,
        date_of_birth=payload.date_of_birth,
        address=payload.address,
        settings=settings,
    )
    return MockVerifyResponse(
        status=result["status"],
        matchScore=int(result["matchScore"]),
        message=result["message"],
        provider=result["provider"],
        checked_at=result["checked_at"],
    )


@router.post("/pan", response_model=MockVerifyResponse)
def verify_pan(payload: MockVerifyRequest, settings: SettingsDep, _user: UserDep) -> MockVerifyResponse:
    return _respond(payload, DocumentType.SYNTHETIC_PAN, settings)


@router.post("/aadhaar", response_model=MockVerifyResponse)
def verify_aadhaar(payload: MockVerifyRequest, settings: SettingsDep, _user: UserDep) -> MockVerifyResponse:
    return _respond(payload, DocumentType.SYNTHETIC_NATIONAL_ID, settings)


@router.post("/document", response_model=MockVerifyResponse)
def verify_document(payload: MockVerifyRequest, settings: SettingsDep, _user: UserDep) -> MockVerifyResponse:
    return _respond(payload, payload.document_type or DocumentType.UNKNOWN, settings)
