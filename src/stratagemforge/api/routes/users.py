from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...domain.users.schemas import LoginRequest, LoginResponse, UserSummary
from .. import deps

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[UserSummary])
def list_users(
    session: Session = Depends(deps.get_db),
    service=Depends(deps.get_user_service),
) -> list[UserSummary]:
    return [UserSummary.from_orm(user) for user in service.list_users(session)]


@router.post("/auth/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    session: Session = Depends(deps.get_db),
    service=Depends(deps.get_user_service),
) -> LoginResponse:
    try:
        user, token = service.authenticate(session, request.email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return LoginResponse(token=token, user=UserSummary.from_orm(user), message="Login successful")
