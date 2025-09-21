from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Tuple
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ...core.config import Settings
from .models import Demo
from .processor import DemoProcessingInput, DemoProcessor
from .repository import DemoRepository


class DemoService:
    """Application service managing demo uploads and queries."""

    def __init__(self, settings: Settings, processor: DemoProcessor | None = None) -> None:
        self.settings = settings
        self.processor = processor or DemoProcessor(settings.processed_data_path)
        self.chunk_size = 4 * 1024 * 1024  # 4MB streaming chunks
        self.settings.ensure_directories()

    async def upload_demo(self, upload: UploadFile, session: Session) -> Tuple[Demo, bool]:
        """Persist an uploaded demo file and generate a parquet summary."""

        if not upload.filename:
            raise ValueError("Uploaded file must have a filename")

        filename = Path(upload.filename).name
        if not filename.lower().endswith(".dem"):
            raise ValueError("Only .dem files are supported")

        checksum, temp_path, total_size = await self._stream_to_disk(upload)

        repo = DemoRepository(session)
        existing = repo.get_by_checksum(checksum)
        if existing:
            temp_path.unlink(missing_ok=True)
            return existing, False

        final_path = self.settings.raw_data_path / f"{checksum}.dem"
        temp_path.replace(final_path)

        demo = Demo(
            id=str(uuid4()),
            original_filename=filename,
            stored_path=str(final_path),
            checksum=checksum,
            size_bytes=total_size,
            content_type=upload.content_type,
            status="uploaded",
            uploaded_at=datetime.utcnow(),
        )
        demo = repo.save(demo)

        processing_input = DemoProcessingInput(
            demo_id=demo.id,
            original_filename=demo.original_filename,
            checksum=demo.checksum,
            size_bytes=demo.size_bytes,
            uploaded_at=demo.uploaded_at,
            raw_path=final_path,
        )

        processing_result = await asyncio.to_thread(self.processor.process, processing_input)
        demo.mark_processed(
            processed_path=str(processing_result.parquet_path),
            processed_at=processing_result.processed_at,
            metadata=processing_result.summary,
        )
        demo = repo.save(demo)
        return demo, True

    def list_demos(self, session: Session) -> list[Demo]:
        return DemoRepository(session).list()

    def get_demo(self, session: Session, demo_id: str) -> Demo | None:
        return DemoRepository(session).get(demo_id)

    async def _stream_to_disk(self, upload: UploadFile) -> Tuple[str, Path, int]:
        checksum = hashlib.sha256()
        temp_path = self.settings.raw_data_path / f"{uuid4().hex}.tmp"
        total_size = 0

        with temp_path.open("wb") as buffer:
            while True:
                chunk = await upload.read(self.chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > self.settings.max_upload_size:
                    buffer.close()
                    temp_path.unlink(missing_ok=True)
                    raise ValueError("Uploaded file exceeds maximum allowed size")
                checksum.update(chunk)
                buffer.write(chunk)

        await upload.close()

        return checksum.hexdigest(), temp_path, total_size
