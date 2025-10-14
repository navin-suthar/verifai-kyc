from __future__ import annotations

from app.core.config import Settings
from app.models.enums import ApplicationStatus, VerificationStatus
from app.services.validation_service import failed_checks


def decide_status(
    *,
    confidence: float,
    validation: list[dict],
    verification: dict | None,
    auto_verify_min: int,
    review_min: int,
) -> tuple[ApplicationStatus, str]:
    error_fails = failed_checks(validation, severity="error")
    warning_fails = failed_checks(validation, severity="warning")
    ver_status = (verification or {}).get("status")
    mock_verified = ver_status == VerificationStatus.VERIFIED.value
    mock_miss = ver_status in {VerificationStatus.NOT_FOUND.value, VerificationStatus.ERROR.value}

    if error_fails and confidence < review_min:
        ids = ", ".join(c["rule_id"] for c in error_fails)
        return (
            ApplicationStatus.REJECTED,
            f"Confidence {confidence:.0f}% is below the {review_min}% investigation floor and error-level rules failed ({ids}).",
        )

    if confidence < review_min:
        return (
            ApplicationStatus.REJECTED,
            f"Confidence {confidence:.0f}% is below the {review_min}% investigation floor. Manual investigation is required before any approval.",
        )

    if error_fails:
        ids = ", ".join(c["rule_id"] for c in error_fails)
        return (
            ApplicationStatus.NEEDS_REVIEW,
            f"Mandatory validation failed ({ids}). Routed to a human reviewer regardless of the {confidence:.0f}% confidence score.",
        )

    if mock_miss and confidence < auto_verify_min:
        return (
            ApplicationStatus.REJECTED if confidence < review_min else ApplicationStatus.NEEDS_REVIEW,
            f"Mock registry returned '{ver_status}' with confidence {confidence:.0f}%. A reviewer must confirm before a decision is final.",
        )

    if mock_miss:
        return (
            ApplicationStatus.NEEDS_REVIEW,
            f"Confidence {confidence:.0f}% is high but the mock registry did not return a match. Human confirmation is required.",
        )

    if ver_status == VerificationStatus.MISMATCH.value or warning_fails:
        band = f"review band [{review_min}%, {auto_verify_min}%)" if confidence < auto_verify_min else "safety override"
        return (
            ApplicationStatus.NEEDS_REVIEW,
            f"Confidence {confidence:.0f}% with a partial mock match or warning-level issues ({band}).",
        )

    if confidence >= auto_verify_min and mock_verified and not error_fails:
        return (
            ApplicationStatus.VERIFIED,
            f"Confidence {confidence:.0f}% ≥ {auto_verify_min}% , all error-level rules passed, and the mock registry returned a match.",
        )

    return (
        ApplicationStatus.NEEDS_REVIEW,
        f"Confidence {confidence:.0f}% is inside the review band [{review_min}%, {auto_verify_min}%).",
    )


def thresholds_payload(settings: Settings) -> dict[str, int]:
    return {
        "auto_verify_min": settings.auto_verify_min_confidence,
        "review_min": settings.review_min_confidence,
    }
