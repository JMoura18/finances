from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.auth import CurrentUserDep, CurrentUser

router = APIRouter()


class MeResponse(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    province: str | None = None
    is_dev: bool = False


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser = CurrentUserDep) -> MeResponse:
    return MeResponse(
        id=str(user.id),
        email=user.email,
        display_name="Jesse" if user.is_dev else None,
        province="ON" if user.is_dev else None,
        is_dev=user.is_dev,
    )
