from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import ApplicationStatus
from app.schemas.application import ApplicationSummary


class StatusCount(BaseModel):
    status: ApplicationStatus
    count: int = Field(ge=0)


class DailyVolume(BaseModel):
    date: str
    verified: int = 0
    rejected: int = 0
    needs_review: int = 0


class DashboardSummary(BaseModel):
    total_applications: int
    verified: int
    rejected: int
    needs_review: int
    pending: int
    average_confidence: float
    success_rate: float
    status_breakdown: list[StatusCount]
    daily_volume: list[DailyVolume]
    recent_applications: list[ApplicationSummary]
