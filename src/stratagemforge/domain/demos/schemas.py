from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DemoSummary(BaseModel):
    id: str
    original_filename: str
    checksum: str
    size_bytes: int
    status: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class DemoDetail(DemoSummary):
    processed_path: Optional[str] = None
    content_type: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class DemoCollection(BaseModel):
    demos: List[DemoSummary]
    count: int


class DemoUploadResponse(DemoDetail):
    message: str


class DemoProcessingStatus(BaseModel):
    demo_id: str
    status: str
    message: str
    processed_at: Optional[datetime] = None
    processed_path: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
