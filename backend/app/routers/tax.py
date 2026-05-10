from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RoomOut(BaseModel):
    account_type: str
    tax_year: int
    total_room_cad: float
    used_cad: float
    available_cad: float


@router.get("/rooms", response_model=list[RoomOut])
async def contribution_rooms() -> list[RoomOut]:
    rows = [
        ("tfsa", 2026, 102000.0, 68420.0),
        ("rrsp", 2026, 88000.0, 62400.0),
        ("fhsa", 2026, 32000.0, 16320.0),
    ]
    return [
        RoomOut(
            account_type=t,
            tax_year=y,
            total_room_cad=tot,
            used_cad=used,
            available_cad=tot - used,
        )
        for (t, y, tot, used) in rows
    ]
