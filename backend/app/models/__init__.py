"""Import all models so Base.metadata knows every table."""

from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.enums import (
    ApplicationStatus,
    AuditAction,
    DocumentType,
    FieldSource,
    ReviewDecision,
    Severity,
    VerificationStatus,
)
from app.models.review import Review
from app.models.verification import VerificationResult

__all__ = [
    "Application",
    "ApplicationStatus",
    "AuditAction",
    "AuditLog",
    "Document",
    "DocumentType",
    "FieldSource",
    "Review",
    "ReviewDecision",
    "Severity",
    "VerificationResult",
    "VerificationStatus",
]
