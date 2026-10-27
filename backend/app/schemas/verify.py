from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import DocumentType, VerificationStatus


class MockVerifyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    document_number: str = Field(..., min_length=4, max_length=40)
    date_of_birth: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=240)
    document_type: DocumentType = DocumentType.UNKNOWN


class MockVerifyResponse(BaseModel):
    status: VerificationStatus
    matchScore: int = Field(ge=0, le=100)
    message: str
    isMock: Literal[True] = True
    provider: str
    checked_at: datetime
