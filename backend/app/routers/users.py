from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class MeResponse(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    province: str | None = None


@router.get("/me", response_model=MeResponse)
async def me() -> MeResponse:
    # Stub. Replace with Firebase token verification + DB lookup.
    return MeResponse(
        id="00000000-0000-0000-0000-000000000001",
        email="jesse@example.com",
        display_name="Jesse",
        province="ON",
    )
