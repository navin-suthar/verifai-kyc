from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbDep, UserDep
from app.schemas.dashboard import DashboardSummary
from app.services import analytics_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: DbDep, _user: UserDep) -> DashboardSummary:
    return analytics_service.dashboard_summary(db)
