from __future__ import annotations

from pathlib import Path as FsPath
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Path, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, PlainTextResponse

from app.api.deps import DbDep, SettingsDep, UserDep, client_ip
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.enums import ApplicationStatus, AuditAction
from app.schemas.application import ApplicationDetail, ApplicationSummary
from app.schemas.common import Paginated
from app.schemas.review import ReviewRequest
from app.services import application_service, audit_service, pipeline_service, review_service
from app.services.document_service import DocumentError

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


@router.post("", response_model=ApplicationDetail, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().rate_limit_upload)
def upload_application(
    request: Request,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    user: UserDep,
    file: Annotated[UploadFile, File(description="Synthetic KYC document")],
) -> ApplicationDetail:
    content = file.file.read(settings.max_upload_bytes + 1)
    try:
        return pipeline_service.process_upload(
            db,
            settings,
            content=content,
            filename=file.filename or "document.txt",
            declared_type=file.content_type,
            actor=user.username,
            ip_address=client_ip(request),
        )
    except DocumentError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(
    application_id: ApplicationId, request: Request, db: DbDep, settings: SettingsDep, user: UserDep
) -> ApplicationDetail:
    app = application_service.get_application(db, application_id)
    if app is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Application not found")
    audit_service.record(
        db,
        action=AuditAction.APPLICATION_VIEWED,
        entity_type="application",
        entity_id=app.id,
        actor=user.username,
        ip_address=client_ip(request),
        commit=True,
    )
    return application_service.to_detail(app, settings)


@router.get("/{application_id}/document")
def get_document(application_id: ApplicationId, db: DbDep, _user: UserDep):
    app = application_service.get_application(db, application_id)
    if app is None or app.document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    doc = app.document
    if doc.storage_path:
        path = FsPath(doc.storage_path)
        if path.is_file():
            return FileResponse(path, media_type=doc.mime_type, filename=doc.filename)
    return PlainTextResponse(doc.extracted_text or "", media_type="text/plain")


@router.post("/{application_id}/review", response_model=ApplicationDetail)
def review_application(
    application_id: ApplicationId,
    payload: ReviewRequest,
    request: Request,
    db: DbDep,
    settings: SettingsDep,
    user: UserDep,
) -> ApplicationDetail:
    app = application_service.get_application(db, application_id)
    if app is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Application not found")
    return review_service.submit_review(
        db,
        settings,
        app,
        decision=payload.decision,
        reviewer=user.username,
        notes=payload.notes,
        ip_address=client_ip(request),
    )
