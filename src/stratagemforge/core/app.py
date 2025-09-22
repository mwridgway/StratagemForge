from __future__ import annotations

from contextlib import asynccontextmanager
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

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # pragma: no cover - simple startup hook
        # Seed initial users at startup
        with session_scope() as session:
            deps.get_user_service().ensure_seed(session)
        yield

    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

    app.include_router(health.router)
    app.include_router(demos.router)
    app.include_router(analysis.router)
    app.include_router(users.router)

    return app
