from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from stratagemforge.domain.demos.processor import DemoProcessingInput, DemoProcessor


def test_processor_creates_parquet(tmp_path):
    processed_dir = tmp_path / "processed"
    processor = DemoProcessor(processed_dir)

    raw_path = tmp_path / "sample.dem"
    raw_path.write_bytes(b"demo data")

    payload = DemoProcessingInput(
        demo_id="demo-1",
        original_filename="sample.dem",
        checksum="abc123",
        size_bytes=raw_path.stat().st_size,
        uploaded_at=datetime.utcnow(),
        raw_path=raw_path,
    )

    result = processor.process(payload)

    assert result.parquet_path.exists()
    df = pd.read_parquet(result.parquet_path)
    assert df.loc[0, "demo_id"] == "demo-1"
    assert df.loc[0, "checksum"] == "abc123"
    assert df.loc[0, "raw_path"] == str(raw_path)
    assert "processed_at" in df.columns
