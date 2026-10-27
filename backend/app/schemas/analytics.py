from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.dashboard import DailyVolume, StatusCount


class TypeCount(BaseModel):
    document_type: str
    count: int = Field(ge=0)


class ConfidenceByStatus(BaseModel):
    status: str
    average_confidence: float
    count: int


class AnalyticsSummary(BaseModel):
    total_applications: int
    verified: int
    rejected: int
    needs_review: int
    pending: int
    average_confidence: float
    success_rate: float
    auto_verified_share: float
    human_reviewed: int
    status_breakdown: list[StatusCount]
    daily_volume: list[DailyVolume]
    document_types: list[TypeCount]
    confidence_by_status: list[ConfidenceByStatus]
    thresholds: dict[str, int]
