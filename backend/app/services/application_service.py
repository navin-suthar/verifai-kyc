from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.schemas.application import (
    ApplicationDetail,
    ApplicationSummary,
    DecisionThresholds,
    DocumentInfo,
    MockVerificationResult,
    ReviewRecord,
)

TEXT_EXCERPT_CHARS = 600


def _base_query():
    return select(Application).options(
        selectinload(Application.document),
        selectinload(Application.verification),
        selectinload(Application.reviews),
    )


def get_application(db: Session, application_id: str) -> Application | None:
    return db.scalar(_base_query().where(Application.id == application_id))


def list_applications(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: ApplicationStatus | None = None,
    query: str | None = None,
) -> tuple[list[Application], int]:
    stmt = _base_query()
    if status:
        stmt = stmt.where(Application.status == status)
    if query:
        like = f"%{query.strip()}%"
        stmt = stmt.where(or_(Application.customer_id.ilike(like), Application.applicant_name.ilike(like)))

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Application.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), int(total)


def next_customer_id(db: Session) -> str:
    last = db.scalar(select(func.max(Application.customer_id)))
    if last and last.startswith("DEMO-") and last[5:].isdigit():
        return f"DEMO-{int(last[5:]) + 1:05d}"
    return "DEMO-10001"


def to_summary(app: Application) -> ApplicationSummary:
    return ApplicationSummary.model_validate(app)


def to_detail(app: Application, settings: Settings) -> ApplicationDetail:
    document = None
    if app.document is not None:
        text = app.document.extracted_text or ""
        document = DocumentInfo(
            id=app.document.id,
            filename=app.document.filename,
            mime_type=app.document.mime_type,
            size_bytes=app.document.size_bytes,
            preview_url=f"{settings.api_prefix}/applications/{app.id}/document",
            text_excerpt=(text[:TEXT_EXCERPT_CHARS] + ("…" if len(text) > TEXT_EXCERPT_CHARS else "")) or None,
        )

    thresholds = app.thresholds or {}
    return ApplicationDetail(
        id=app.id,
        customer_id=app.customer_id,
        applicant_name=app.applicant_name,
        document_type=app.document_type,
        document_number_masked=app.document_number_masked,
        status=app.status,
        confidence=app.confidence,
        created_at=app.created_at,
        updated_at=app.updated_at,
        fields=app.fields,
        validation=app.validation,
        verification=MockVerificationResult.model_validate(app.verification) if app.verification else None,
        issues=app.issues,
        explanation=app.explanation,
        decision_reason=app.decision_reason,
        document=document,
        review=ReviewRecord.model_validate(app.latest_review) if app.latest_review else None,
        thresholds=DecisionThresholds(
            auto_verify_min=int(thresholds.get("auto_verify_min", settings.auto_verify_min_confidence)),
            review_min=int(thresholds.get("review_min", settings.review_min_confidence)),
        ),
    )
