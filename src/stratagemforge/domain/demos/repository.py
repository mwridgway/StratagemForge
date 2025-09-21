from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Demo


class DemoRepository:
    """Data access layer for demo entities."""

    def __init__(self, session: Session):
        self.session = session

    def list(self) -> List[Demo]:
        stmt = select(Demo).order_by(Demo.uploaded_at.desc())
        return list(self.session.scalars(stmt).all())

    def get(self, demo_id: str) -> Optional[Demo]:
        return self.session.get(Demo, demo_id)

    def get_by_checksum(self, checksum: str) -> Optional[Demo]:
        stmt = select(Demo).where(Demo.checksum == checksum)
        return self.session.scalars(stmt).first()

    def save(self, demo: Demo) -> Demo:
        self.session.add(demo)
        self.session.commit()
        self.session.refresh(demo)
        return demo
