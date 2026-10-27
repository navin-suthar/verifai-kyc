from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbDep, SettingsDep, UserDep
from app.schemas.analytics import AnalyticsSummary
from app.schemas.settings_public import PublicSettings
from app.services import analytics_service

router = APIRouter(tags=["analytics"])

PRIVACY_NOTICE = (
    "This is a portfolio demo. Do not upload real identity documents. "
    "All verification responses are produced by a local mock service and have no legal meaning."
)


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(db: DbDep, _user: UserDep) -> AnalyticsSummary:
    return analytics_service.analytics_summary(db)


@router.get("/settings/public", response_model=PublicSettings)
def public_settings(settings: SettingsDep, _user: UserDep) -> PublicSettings:
    return PublicSettings(
        app_name=settings.app_name,
        auto_verify_min_confidence=settings.auto_verify_min_confidence,
        review_min_confidence=settings.review_min_confidence,
        max_upload_bytes=settings.max_upload_bytes,
        allowed_extensions=settings.allowed_extensions,
        llm_enabled=settings.llm_enabled,
        ollama_model=settings.ollama_model,
        privacy_notice=PRIVACY_NOTICE,
    )
