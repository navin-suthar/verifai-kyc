from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.api.deps import DbDep, SettingsDep, UserDep
from app.models.enums import ApplicationStatus
from app.schemas.application import ApplicationDetail, ApplicationSummary
from app.schemas.common import Paginated
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])

ApplicationId = Annotated[str, Path(pattern=r"^[a-f0-9]{32}$", description="Application id (hex uuid)")]


@router.get("", response_model=Paginated[ApplicationSummary])
def list_applications(
    db: DbDep,
    _user: UserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=80)] = None,
) -> Paginated[ApplicationSummary]:
    rows, total = application_service.list_applications(
        db, page=page, page_size=page_size, status=status_filter, query=q
    )
    return Paginated(
        items=[application_service.to_summary(a) for a in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(
    application_id: ApplicationId, db: DbDep, settings: SettingsDep, _user: UserDep
) -> ApplicationDetail:
    app = application_service.get_application(db, application_id)
    if app is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application_service.to_detail(app, settings)
