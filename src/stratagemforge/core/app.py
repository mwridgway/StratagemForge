from __future__ import annotations

from fastapi import FastAPI

from ..api import deps
from ..api.routes import analysis, demos, health, users
from .config import Settings, get_settings
from .database import Base, create_all, init_engine, session_scope


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    settings.ensure_directories()
    deps.configure(settings)
    init_engine(settings)
    create_all()

    app = FastAPI(title=settings.app_name, version=settings.version)

    app.include_router(health.router)
    app.include_router(demos.router)
    app.include_router(analysis.router)
    app.include_router(users.router)

    @app.on_event("startup")
    def seed_users() -> None:  # pragma: no cover - simple startup hook
        with session_scope() as session:
            deps.get_user_service().ensure_seed(session)

    return app
