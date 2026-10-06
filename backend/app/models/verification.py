from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, utcnow
from app.models.enums import VerificationStatus

if TYPE_CHECKING:
    from app.models.application import Application


class VerificationResult(Base, IdMixin):
    """Outcome of the MOCK external verification call for an application."""

    __tablename__ = "verification_results"

    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, native_enum=False, length=20), nullable=False
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    raw_response: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    application: Mapped[Application] = relationship(back_populates="verification")
