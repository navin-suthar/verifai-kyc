from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, utcnow
from app.models.enums import ReviewDecision

if TYPE_CHECKING:
    from app.models.application import Application


class Review(Base, IdMixin):
    """A human reviewer's decision on an application (append-only history)."""

    __tablename__ = "reviews"

    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision: Mapped[ReviewDecision] = mapped_column(Enum(ReviewDecision, native_enum=False, length=20), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(80), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    application: Mapped[Application] = relationship(back_populates="reviews")
