"""Session token helpers (HS256 JWT) and constant-time credential checks."""

from __future__ import annotations

import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import Settings

ALGORITHM = "HS256"


def verify_demo_credentials(settings: Settings, username: str, password: str) -> bool:
    """Compare both fields in constant time to avoid timing side channels."""
    user_ok = hmac.compare_digest(username.encode(), settings.demo_username.encode())
    pass_ok = hmac.compare_digest(password.encode(), settings.demo_password.encode())
    return user_ok and pass_ok


def create_session_token(settings: Settings, *, username: str, role: str, display_name: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": username,
        "role": role,
        "name": display_name,
        "iat": now,
        "exp": now + timedelta(minutes=settings.session_ttl_minutes),
        "jti": uuid.uuid4().hex,
        "iss": "verifai",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_session_token(settings: Settings, token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            issuer="verifai",
            options={"require": ["exp", "sub", "iat"]},
        )
    except jwt.PyJWTError:
        return None
