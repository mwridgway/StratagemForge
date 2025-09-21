from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserSummary(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    token: str
    user: UserSummary
    message: str
