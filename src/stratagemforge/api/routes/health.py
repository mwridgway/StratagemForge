from __future__ import annotations

from fastapi import APIRouter

from ...core.config import Settings
from .. import deps

router = APIRouter()


@router.get("/", tags=["health"])
def root() -> dict[str, object]:
    settings = deps.get_active_settings()
    return {
        "service": settings.app_name,
        "status": "running",
        "version": settings.version,
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "config": "/config",
            "demos": "/api/demos",
            "analysis": "/api/analysis",
            "users": "/api/users",
        },
    }


@router.get("/health", tags=["health"])
def health_check() -> dict[str, object]:
    settings = deps.get_active_settings()
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
    }


@router.get("/ready", tags=["health"])
def ready_check() -> dict[str, object]:
    return {"status": "ready"}


@router.get("/config", tags=["health"])
def config() -> dict[str, object]:
    settings = deps.get_active_settings()
    masked_db = "configured" if settings.database_url else "not configured"
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "database": masked_db,
        "data_directory": str(settings.data_dir),
    }
