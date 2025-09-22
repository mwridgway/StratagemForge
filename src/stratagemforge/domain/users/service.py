from __future__ import annotations

import base64
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import Settings
from .models import User


class UserService:
    """Simplified user management for the modular monolith."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def ensure_seed(self, session: Session) -> None:
        """Seed the database with a demo user if no accounts exist."""

        has_users = session.execute(select(User.id)).first()
        if has_users:
            return

        demo_user = User(
            email="analyst@example.com",
            display_name="Demo Analyst",
            role="admin",
        )
        session.add(demo_user)
        session.commit()

    def list_users(self, session: Session) -> list[User]:
        stmt = select(User).order_by(User.created_at)
        return list(session.scalars(stmt).all())

    def authenticate(self, session: Session, email: str) -> tuple[User, str]:
        stmt = select(User).where(User.email == email)
        user = session.scalars(stmt).first()
        if not user:
            raise ValueError("User not found")

        user.last_login_at = datetime.now(timezone.utc)
        session.add(user)
        session.commit()
        session.refresh(user)

        token = base64.b64encode(f"{user.id}:{user.email}".encode()).decode()
        return user, token
