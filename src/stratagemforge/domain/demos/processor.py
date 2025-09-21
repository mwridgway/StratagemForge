from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd


@dataclass
class DemoProcessingInput:
    demo_id: str
    original_filename: str
    checksum: str
    size_bytes: int
    uploaded_at: datetime
    raw_path: Path


@dataclass
class DemoProcessingResult:
    parquet_path: Path
    processed_at: datetime
    summary: Dict[str, Any]


class DemoProcessor:
    """Convert uploaded demo files into parquet summaries for analysis."""

    def __init__(self, processed_dir: Path) -> None:
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def process(self, payload: DemoProcessingInput) -> DemoProcessingResult:
        """Produce a minimal parquet dataset describing the uploaded demo."""

        processed_at = datetime.utcnow()
        parquet_path = self.processed_dir / f"{payload.demo_id}.parquet"

        # Derive lightweight metadata for quick inspection
        summary = {
            "demo_id": payload.demo_id,
            "original_filename": payload.original_filename,
            "checksum": payload.checksum,
            "size_bytes": payload.size_bytes,
            "uploaded_at": payload.uploaded_at.isoformat(),
            "processed_at": processed_at.isoformat(),
            "raw_path": str(payload.raw_path),
        }

        df = pd.DataFrame([summary])
        df.to_parquet(parquet_path, index=False)

        return DemoProcessingResult(parquet_path=parquet_path, processed_at=processed_at, summary=summary)
