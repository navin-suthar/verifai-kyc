"""Aggregations for the dashboard and analytics pages (DB-agnostic)."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.schemas.application import ApplicationSummary
from app.schemas.dashboard import DailyVolume, DashboardSummary, StatusCount
from app.services.application_service import list_applications

VOLUME_DAYS = 14


def _status_counts(db: Session) -> dict[ApplicationStatus, int]:
    rows = db.execute(select(Application.status, func.count()).group_by(Application.status)).all()
    counts = dict.fromkeys(ApplicationStatus, 0)
    for status, count in rows:
        counts[ApplicationStatus(status)] = int(count)
    return counts


def _daily_volume(db: Session, days: int = VOLUME_DAYS) -> list[DailyVolume]:
    since = datetime.now(UTC) - timedelta(days=days - 1)
    since = since.replace(hour=0, minute=0, second=0, microsecond=0)
    rows = db.execute(select(Application.created_at, Application.status).where(Application.created_at >= since)).all()

    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"verified": 0, "rejected": 0, "needs_review": 0})
    for created_at, status in rows:
        key = created_at.date().isoformat()
        if status in ("verified", "rejected", "needs_review"):
            buckets[key][str(status)] += 1

    out: list[DailyVolume] = []
    for i in range(days):
        day = (since + timedelta(days=i)).date().isoformat()
        out.append(DailyVolume(date=day, **buckets[day]))
    return out


def analytics_summary(db: Session) -> "AnalyticsSummary":
    from app.models.enums import ReviewDecision
    from app.models.review import Review
    from app.schemas.analytics import AnalyticsSummary, ConfidenceByStatus, TypeCount
    from app.core.config import get_settings

    settings = get_settings()
    dash = dashboard_summary(db)
    type_rows = db.execute(select(Application.document_type, func.count()).group_by(Application.document_type)).all()
    conf_rows = db.execute(
        select(Application.status, func.avg(Application.confidence), func.count()).group_by(Application.status)
    ).all()
    human_reviewed = db.scalar(select(func.count()).select_from(Review)) or 0
    decided = dash.verified + dash.rejected
    # Approximated: verified apps without an approve review are treated as auto-verified.
    approved = db.scalar(select(func.count()).select_from(Review).where(Review.decision == ReviewDecision.APPROVE)) or 0
    auto_share = ((dash.verified - int(approved)) / decided * 100) if decided else 0.0

    return AnalyticsSummary(
        total_applications=dash.total_applications,
        verified=dash.verified,
        rejected=dash.rejected,
        needs_review=dash.needs_review,
        pending=dash.pending,
        average_confidence=dash.average_confidence,
        success_rate=dash.success_rate,
        auto_verified_share=round(max(0.0, auto_share), 1),
        human_reviewed=int(human_reviewed),
        status_breakdown=dash.status_breakdown,
        daily_volume=dash.daily_volume,
        document_types=[TypeCount(document_type=str(t), count=int(c)) for t, c in type_rows],
        confidence_by_status=[
            ConfidenceByStatus(
                status=str(status),
                average_confidence=round(float(avg or 0), 1),
                count=int(count),
            )
            for status, avg, count in conf_rows
        ],
        thresholds={
            "auto_verify_min": settings.auto_verify_min_confidence,
            "review_min": settings.review_min_confidence,
        },
    )


def dashboard_summary(db: Session) -> DashboardSummary:
    counts = _status_counts(db)
    total = sum(counts.values())
    verified = counts[ApplicationStatus.VERIFIED]
    rejected = counts[ApplicationStatus.REJECTED]
    needs_review = counts[ApplicationStatus.NEEDS_REVIEW]
    pending = counts[ApplicationStatus.PENDING] + counts[ApplicationStatus.PROCESSING]

    avg_conf = db.scalar(select(func.avg(Application.confidence)).where(Application.confidence.is_not(None)))
    decided = verified + rejected
    success_rate = (verified / decided * 100) if decided else 0.0

    recent, _ = list_applications(db, page=1, page_size=8)

    breakdown = [
        StatusCount(status=s, count=counts[s])
        for s in (
            ApplicationStatus.VERIFIED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.NEEDS_REVIEW,
            ApplicationStatus.PENDING,
            ApplicationStatus.PROCESSING,
        )
        if counts[s] > 0
    ]

    return DashboardSummary(
        total_applications=total,
        verified=verified,
        rejected=rejected,
        needs_review=needs_review,
        pending=pending,
        average_confidence=round(float(avg_conf or 0.0), 1),
        success_rate=round(success_rate, 1),
        status_breakdown=breakdown,
        daily_volume=_daily_volume(db),
        recent_applications=[ApplicationSummary.model_validate(a) for a in recent],
    )
