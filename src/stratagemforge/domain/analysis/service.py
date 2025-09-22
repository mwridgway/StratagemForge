from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pandas as pd
from sqlalchemy.orm import Session

from ...core.config import Settings
from ..demos.models import Demo
from ..demos.repository import DemoRepository
from .schemas import AnalysisRequest, AnalysisResult


class AnalysisService:
    """Perform lightweight analytics on processed demo files."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_available_demos(self, session: Session) -> list[Demo]:
        return DemoRepository(session).list()

    def run_analysis(self, session: Session, request: AnalysisRequest) -> AnalysisResult:
        repository = DemoRepository(session)
        demo = repository.get(request.demo_id)
        if not demo:
            raise ValueError(f"Demo {request.demo_id} not found")
        if not demo.processed_path:
            raise ValueError("Demo has not been processed yet")

        parquet_path = Path(demo.processed_path)
        if not parquet_path.exists():
            raise FileNotFoundError(f"Processed parquet file missing at {parquet_path}")

        df = pd.read_parquet(parquet_path)

        results: Dict[str, object] = {
            "row_count": int(len(df)),
            "columns": list(df.columns),
            "metadata": demo.extra_metadata or {},
            "file": {
                "original_filename": demo.original_filename,
                "checksum": demo.checksum,
                "size_bytes": demo.size_bytes,
            },
        }

        if "size_bytes" in df.columns:
            results["size_statistics"] = {
                "min_size": int(df["size_bytes"].min()),
                "max_size": int(df["size_bytes"].max()),
                "mean_size": float(df["size_bytes"].mean()),
            }

        return AnalysisResult(
            demo_id=demo.id,
            analysis_type=request.analysis_type,
            status="completed",
            results=results,
            message=f"Analysis completed for demo {demo.id}",
            generated_at=datetime.now(timezone.utc),
        )
