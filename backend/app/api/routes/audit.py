from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbDep, UserDep
from app.schemas.audit import AuditLogEntry
from app.schemas.common import Paginated
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=Paginated[AuditLogEntry])
def list_audit_logs(
    db: DbDep,
    _user: UserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    action: Annotated[str | None, Query(max_length=64)] = None,
    actor: Annotated[str | None, Query(max_length=80)] = None,
    entity_id: Annotated[str | None, Query(max_length=64)] = None,
) -> Paginated[AuditLogEntry]:
    rows, total = audit_service.list_logs(
        db, page=page, page_size=page_size, action=action, actor=actor, entity_id=entity_id
    )
    return Paginated(
        items=[AuditLogEntry.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
