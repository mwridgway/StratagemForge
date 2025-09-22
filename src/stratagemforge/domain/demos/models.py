from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base


class Demo(Base):
    """ORM model representing an uploaded demo file."""

    __tablename__ = "demos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    processed_path: Mapped[Optional[str]] = mapped_column(String(1024))
    checksum: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="uploaded", nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    def mark_processed(self, processed_path: str, processed_at: datetime, metadata: Dict[str, Any]) -> None:
        self.status = "processed"
        self.processed_path = processed_path
        self.processed_at = processed_at
        self.extra_metadata = metadata
