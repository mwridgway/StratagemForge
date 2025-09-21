from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import Settings, get_settings


class Base(DeclarativeBase):
    """Base class for declarative ORM models."""


_engine = None
_SessionLocal: Optional[sessionmaker[Session]] = None


def init_engine(settings: Optional[Settings] = None) -> None:
    """Initialise the global SQLAlchemy engine and session factory."""

    global _engine, _SessionLocal
    settings = settings or get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    _engine = create_engine(settings.database_url, echo=settings.debug, future=True, connect_args=connect_args)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def get_engine():
    if _engine is None:
        init_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None
    return _SessionLocal


@contextmanager
def session_scope(settings: Optional[Settings] = None) -> Generator[Session, None, None]:
    factory = get_session_factory() if settings is None else sessionmaker(
        bind=create_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
            connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
        ),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_all() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
