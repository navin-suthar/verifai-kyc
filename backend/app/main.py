from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_ctx
from app.core.rate_limit import limiter
from app.database.base import Base
from app.database.session import engine

logger = logging.getLogger(__name__)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    import app.models  # noqa: F401  (register tables)

    Base.metadata.create_all(bind=engine)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    if settings.environment == "development":
        from app.database.seed import seed
        from app.database.session import SessionLocal

        with SessionLocal() as db:
            created = seed(db)
            if created:
                logger.info("seeded %s synthetic applications", created)
        try:
            from app.services import rag_service

            n = rag_service.ingest_policies(settings)
            logger.info("rag knowledge base ready (%s chunks)", n)
        except Exception as exc:  # noqa: BLE001
            logger.info("rag ingest skipped: %s", exc)
    logger.info(
        "%s v%s starting (env=%s, db=%s)",
        settings.app_name,
        __version__,
        settings.environment,
        "sqlite" if settings.is_sqlite else "postgresql",
    )
    yield
    logger.info("shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Portfolio demo: AI-powered KYC document intelligence with mock verification. "
            "Processes synthetic documents only."
        ),
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-Request-Id"],
        expose_headers=["X-Request-Id", "Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if 8 <= len(incoming) <= 64 and incoming.isascii() else uuid.uuid4().hex
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers["X-Request-Id"] = rid
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": [str(p) for p in e.get("loc", []) if p != "body"], "msg": e.get("msg", "invalid")}
            for e in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": errors, "message": "Request validation failed"})

    @app.exception_handler(Exception)
    async def unhandled_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error: %s", exc.__class__.__name__)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
