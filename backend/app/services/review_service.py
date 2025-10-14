from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Application, ApplicationStatus, AuditAction, Review, ReviewDecision
from app.schemas.application import ApplicationDetail
from app.services import application_service, audit_service


def submit_review(
    db: Session,
    settings: Settings,
    app: Application,
    *,
    decision: ReviewDecision,
    reviewer: str,
    notes: str | None,
    ip_address: str | None,
) -> ApplicationDetail:
    if app.status not in {ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.PENDING, ApplicationStatus.PROCESSING}:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Only applications awaiting review can receive a reviewer decision.",
        )

    clean_notes = (notes or "").strip()[:2000] or None
    review = Review(decision=decision, reviewer=reviewer, notes=clean_notes)
    app.reviews.append(review)

    if decision == ReviewDecision.APPROVE:
        app.status = ApplicationStatus.VERIFIED
        app.decision_reason = f"Approved by reviewer {reviewer}."
    elif decision == ReviewDecision.REJECT:
        app.status = ApplicationStatus.REJECTED
        app.decision_reason = f"Rejected by reviewer {reviewer}."
    else:
        app.status = ApplicationStatus.NEEDS_REVIEW
        app.decision_reason = f"Reviewer {reviewer} requested more information."

    if clean_notes:
        app.explanation = f"{app.explanation or ''}\n\nReviewer note: {clean_notes}".strip()

    audit_service.record(
        db,
        action=AuditAction.REVIEW_SUBMITTED,
        entity_type="application",
        entity_id=app.id,
        actor=reviewer,
        details={"decision": decision.value, "has_notes": bool(clean_notes)},
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(app)
    return application_service.to_detail(app, settings)
