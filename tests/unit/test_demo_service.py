from __future__ import annotations

import io
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import UploadFile

from stratagemforge.core.config import Settings
from stratagemforge.core.database import Base
from stratagemforge.domain.demos.processor import DemoProcessor
from stratagemforge.domain.demos.service import DemoService


@pytest.fixture
def service_with_session(tmp_path):
    data_dir = tmp_path / "data"
    settings = Settings(data_dir=data_dir, database_url=f"sqlite:///{tmp_path}/test.db")
    settings.ensure_directories()

    engine = create_engine(settings.database_url, future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, future=True, autoflush=False, autocommit=False, expire_on_commit=False)
    session = SessionLocal()

    service = DemoService(settings, processor=DemoProcessor(settings.processed_data_path))
    try:
        yield service, session, settings
    finally:
        session.close()


@pytest.mark.asyncio
async def test_upload_creates_demo(service_with_session):
    service, session, settings = service_with_session
    upload = UploadFile(filename="match.dem", file=io.BytesIO(b"demo data"))

    demo, created = await service.upload_demo(upload, session)

    assert created is True
    assert demo.processed_path is not None
    assert Path(demo.processed_path).exists()
    assert demo.extra_metadata["checksum"] == demo.checksum


@pytest.mark.asyncio
async def test_duplicate_upload_returns_existing(service_with_session):
    service, session, settings = service_with_session

    first_upload = UploadFile(filename="match.dem", file=io.BytesIO(b"demo data"))
    first_demo, created_first = await service.upload_demo(first_upload, session)
    assert created_first is True

    duplicate_upload = UploadFile(filename="match.dem", file=io.BytesIO(b"demo data"))
    second_demo, created_second = await service.upload_demo(duplicate_upload, session)

    assert created_second is False
    assert second_demo.id == first_demo.id
