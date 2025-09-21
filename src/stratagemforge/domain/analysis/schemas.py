from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    demo_id: str
    analysis_type: str = Field(default="basic", description="Type of analysis to perform")


class AnalysisResult(BaseModel):
    demo_id: str
    analysis_type: str
    status: str
    results: Dict[str, Any]
    message: str
    generated_at: datetime


class AnalysisConfig(BaseModel):
    port: int
    database_url: str
    data_path: str
    message: str
