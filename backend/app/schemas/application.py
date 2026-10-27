from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import (
    ApplicationStatus,
    DocumentType,
    FieldSource,
    ReviewDecision,
    Severity,
    VerificationStatus,
)
from app.schemas.common import ORMModel


class ExtractedField(BaseModel):
    name: str
    label: str
    value: str | None
    confidence: float = Field(ge=0, le=100)
    source: FieldSource


class ValidationCheck(BaseModel):
    rule_id: str
    name: str
    passed: bool
    severity: Severity
    message: str


class MockVerificationResult(ORMModel):
    provider: str
    status: VerificationStatus
    match_score: float = Field(ge=0, le=100)
    message: str
    is_mock: Literal[True] = True
    checked_at: datetime


class ReviewRecord(ORMModel):
    id: str
    decision: ReviewDecision
    reviewer: str
    notes: str | None
    created_at: datetime


class DecisionThresholds(BaseModel):
    auto_verify_min: int = Field(ge=0, le=100)
    review_min: int = Field(ge=0, le=100)


class DocumentInfo(ORMModel):
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    preview_url: str | None = None
    text_excerpt: str | None = None


class ApplicationSummary(ORMModel):
    id: str
    customer_id: str
    applicant_name: str | None
    document_type: DocumentType
    document_number_masked: str | None
    status: ApplicationStatus
    confidence: float | None
    created_at: datetime
    updated_at: datetime


class ApplicationDetail(ApplicationSummary):
    fields: list[ExtractedField]
    validation: list[ValidationCheck]
    verification: MockVerificationResult | None
    issues: list[str]
    explanation: str | None
    decision_reason: str | None
    document: DocumentInfo | None
    review: ReviewRecord | None
    thresholds: DecisionThresholds
