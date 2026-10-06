"""Shared slowapi limiter. Keyed by client IP (X-Forwarded-For aware)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import get_settings


def client_identifier(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=client_identifier,
    default_limits=[get_settings().rate_limit_default],
    headers_enabled=True,
    enabled=get_settings().environment != "test",
)
