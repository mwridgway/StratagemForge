from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "StratagemForge"
    debug: bool = False
    version: str = "0.1.0"
    database_url: str = "sqlite:///./data/stratagemforge.db"
    data_dir: Path = Path("data")
    raw_dir_name: str = "uploads"
    processed_dir_name: str = "processed"
    max_upload_size: int = 1_073_741_824  # 1GB default limit

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", case_sensitive=False)

    @field_validator("data_dir", mode="before")
    @classmethod
    def _convert_data_dir(cls, value: Any) -> Path:
        if isinstance(value, Path):
            return value
        return Path(str(value))

    @property
    def raw_data_path(self) -> Path:
        return self.data_dir / self.raw_dir_name

    @property
    def processed_data_path(self) -> Path:
        return self.data_dir / self.processed_dir_name

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.raw_data_path, self.processed_data_path):
            path.mkdir(parents=True, exist_ok=True)


def _build_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return _build_settings()
