from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantAskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    application_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")


class ChatSource(BaseModel):
    document: str
    section: str | None
    chunk_id: str
    score: float
    excerpt: str


class ChatAnswer(BaseModel):
    answer: str
    sources: list[ChatSource]
    grounded: bool
    model: str
    latency_ms: int
