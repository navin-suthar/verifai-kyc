from __future__ import annotations

from enum import StrEnum


class ApplicationStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class DocumentType(StrEnum):
    SYNTHETIC_PAN = "synthetic_pan"
    SYNTHETIC_NATIONAL_ID = "synthetic_national_id"
    SYNTHETIC_PASSPORT = "synthetic_passport"
    SYNTHETIC_UTILITY_BILL = "synthetic_utility_bill"
    UNKNOWN = "unknown"


class FieldSource(StrEnum):
    RULE = "rule"
    OCR = "ocr"
    LLM = "llm"
    MANUAL = "manual"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    NOT_FOUND = "not_found"
    MISMATCH = "mismatch"
    ERROR = "error"
    SKIPPED = "skipped"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_INFO = "request_info"


class AuditAction(StrEnum):
    LOGIN = "auth.login"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_REJECTED = "document.rejected"
    EXTRACTION_COMPLETED = "pipeline.extraction_completed"
    VALIDATION_COMPLETED = "pipeline.validation_completed"
    VERIFICATION_COMPLETED = "pipeline.verification_completed"
    DECISION_MADE = "pipeline.decision_made"
    REVIEW_SUBMITTED = "review.submitted"
    ASSISTANT_QUERY = "assistant.query"
    APPLICATION_VIEWED = "application.viewed"
