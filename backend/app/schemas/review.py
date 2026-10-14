from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import ReviewDecision


class ReviewRequest(BaseModel):
    decision: ReviewDecision
    notes: str | None = Field(default=None, max_length=2000)
