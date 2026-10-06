"""FastAPI dependencies: settings, DB session, authenticated user, CSRF guard."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import decode_session_token
from app.database.session import get_db
from app.schemas.auth import CurrentUser

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]


def _extract_token(request: Request, settings: Settings) -> tuple[str | None, str]:
    """Return (token, source) where source is 'bearer' or 'cookie'."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip(), "bearer"
    return request.cookies.get(settings.session_cookie_name), "cookie"


def get_current_user(request: Request, settings: SettingsDep) -> CurrentUser:
    token, source = _extract_token(request, settings)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = decode_session_token(settings, token)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Session is invalid or has expired")

    # CSRF defence for cookie sessions: browsers cannot add custom headers cross-site
    # without a CORS preflight, so requiring X-Requested-With blocks forged form posts.
    if source == "cookie" and request.method not in SAFE_METHODS:
        if request.headers.get("x-requested-with") != "XMLHttpRequest":
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Missing CSRF protection header")

    return CurrentUser(
        username=payload["sub"], role=payload.get("role", "analyst"), display_name=payload.get("name", "")
    )


UserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_role(*roles: str):
    def _checker(user: UserDep) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _checker


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
