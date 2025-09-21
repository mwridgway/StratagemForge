from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from ..core.config import Settings, get_settings
from ..core.database import get_session, init_engine
from ..domain.analysis.service import AnalysisService
from ..domain.demos.service import DemoService
from ..domain.users.service import UserService

_demo_service: DemoService | None = None
_analysis_service: AnalysisService | None = None
_user_service: UserService | None = None
_current_settings: Settings | None = None


def configure(settings: Settings | None = None) -> None:
    global _demo_service, _analysis_service, _user_service, _current_settings
    _current_settings = settings or get_settings()
    init_engine(_current_settings)
    _demo_service = DemoService(_current_settings)
    _analysis_service = AnalysisService(_current_settings)
    _user_service = UserService(_current_settings)


def _ensure_configured() -> Settings:
    if _current_settings is None:
        configure()
    assert _current_settings is not None
    return _current_settings


def get_db(session: Session = Depends(get_session)) -> Session:
    return session


def get_demo_service() -> DemoService:
    if _demo_service is None:
        configure()
    assert _demo_service is not None
    return _demo_service


def get_analysis_service() -> AnalysisService:
    if _analysis_service is None:
        configure()
    assert _analysis_service is not None
    return _analysis_service


def get_user_service() -> UserService:
    if _user_service is None:
        configure()
    assert _user_service is not None
    return _user_service


def get_active_settings() -> Settings:
    return _ensure_configured()
