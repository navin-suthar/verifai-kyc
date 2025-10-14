from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin
from app.models.enums import ApplicationStatus, DocumentType

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.review import Review
    from app.models.verification import VerificationResult


class Application(Base, IdMixin, TimestampMixin):
    __tablename__ = "applications"

    customer_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    applicant_name: Mapped[str | None] = mapped_column(String(120))
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False, length=40), default=DocumentType.UNKNOWN, nullable=False
    )
    # We store only a masked rendering plus a salted hash (for duplicate detection).
    document_number_masked: Mapped[str | None] = mapped_column(String(40))
    document_number_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=20),
        default=ApplicationStatus.PENDING,
        nullable=False,
        index=True,
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    decision_reason: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)

    # Document-shaped payloads that are always read together with the application.
    fields: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    validation: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    issues: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    thresholds: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    document: Mapped[Document | None] = relationship(
        back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    verification: Mapped[VerificationResult | None] = relationship(
        back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="Review.created_at.desc()"
    )

    __table_args__ = (Index("ix_applications_created_at", "created_at"),)

    @property
    def latest_review(self) -> Review | None:
        return self.reviews[0] if self.reviews else None
