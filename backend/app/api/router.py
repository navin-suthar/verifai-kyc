from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import analytics, applications, assistant, audit, auth, dashboard, health, verify

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(applications.router)
api_router.include_router(verify.router)
api_router.include_router(assistant.router)
api_router.include_router(audit.router)
api_router.include_router(analytics.router)
