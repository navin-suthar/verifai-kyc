from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.api.deps import DbDep, SettingsDep
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: DbDep, settings: SettingsDep) -> HealthResponse:
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:  # pragma: no cover - only on infra failure
        checks["database"] = "error"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return HealthResponse(
        status=overall,
        environment=settings.environment,
        version=__version__,
        database="sqlite" if settings.is_sqlite else "postgresql",
        checks=checks,
    )
