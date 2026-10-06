from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import DbDep, SettingsDep, UserDep, client_ip
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import create_session_token, verify_demo_credentials
from app.models.enums import AuditAction
from app.schemas.auth import CurrentUser, LoginRequest
from app.schemas.common import MessageResponse
from app.services import audit_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=CurrentUser)
@limiter.limit(get_settings().rate_limit_login)
def login(request: Request, response: Response, payload: LoginRequest, db: DbDep, settings: SettingsDep) -> CurrentUser:
    ip = client_ip(request)
    if not verify_demo_credentials(settings, payload.username, payload.password):
        audit_service.record(
            db,
            action=AuditAction.LOGIN_FAILED,
            entity_type="user",
            entity_id=payload.username[:64],
            actor="anonymous",
            ip_address=ip,
            commit=True,
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_session_token(
        settings,
        username=settings.demo_username,
        role=settings.demo_role,
        display_name=settings.demo_display_name,
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_minutes * 60,
        path="/",
    )
    audit_service.record(
        db,
        action=AuditAction.LOGIN,
        entity_type="user",
        entity_id=settings.demo_username,
        actor=settings.demo_username,
        ip_address=ip,
        commit=True,
    )
    return CurrentUser(
        username=settings.demo_username, role=settings.demo_role, display_name=settings.demo_display_name
    )


@router.get("/me", response_model=CurrentUser)
def me(user: UserDep) -> CurrentUser:
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, user: UserDep, db: DbDep, settings: SettingsDep) -> MessageResponse:
    response.delete_cookie(settings.session_cookie_name, path="/")
    audit_service.record(
        db,
        action=AuditAction.LOGOUT,
        entity_type="user",
        entity_id=user.username,
        actor=user.username,
        ip_address=client_ip(request),
        commit=True,
    )
    return MessageResponse(message="Signed out")
