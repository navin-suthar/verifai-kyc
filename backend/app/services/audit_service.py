from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import request_id_ctx
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction

logger = logging.getLogger(__name__)

_SENSITIVE_KEYS = {"password", "token", "secret", "document_number", "authorization", "cookie"}


def _scrub(details: dict[str, Any]) -> dict[str, Any]:
    return {k: ("[redacted]" if k.lower() in _SENSITIVE_KEYS else v) for k, v in details.items()}


def record(
    db: Session,
    *,
    action: AuditAction | str,
    entity_type: str,
    entity_id: str | None = None,
    actor: str = "system",
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    commit: bool = False,
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        action=str(action),
        entity_type=entity_type,
        entity_id=entity_id,
        details=_scrub(details or {}),
        ip_address=ip_address,
        request_id=request_id_ctx.get(),
    )
    db.add(entry)
    if commit:
        db.commit()
    logger.info("audit %s %s/%s by %s", entry.action, entity_type, entity_id, actor)
    return entry


def list_logs(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 25,
    action: str | None = None,
    entity_id: str | None = None,
    actor: str | None = None,
) -> tuple[list[AuditLog], int]:
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor:
        stmt = stmt.where(AuditLog.actor == actor)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return list(rows), int(total)
