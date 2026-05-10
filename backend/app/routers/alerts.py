from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.database import get_db
from app.models import Alert

router = APIRouter()


class AlertOut(BaseModel):
    id: str
    severity: str
    title: str
    body: str
    category: str
    is_read: bool
    created_at: datetime


SEED = [
    AlertOut(
        id="a-seed-1", severity="warn", category="concentration",
        title="Tech sector concentration",
        body="Tech is 38% of portfolio. Not a recommendation — just an observation.",
        is_read=False, created_at=datetime(2026, 5, 9, 21, 14),
    ),
    AlertOut(
        id="a-seed-2", severity="info", category="rebalance",
        title="Bonds underweight",
        body="Bonds are 8% vs 20% target.",
        is_read=False, created_at=datetime(2026, 5, 8, 9, 30),
    ),
]


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[AlertOut]:
    rows = await db.execute(
        select(Alert)
        .where(Alert.user_id == user.id)
        .order_by(Alert.created_at.desc())
        .limit(100)
    )
    items = rows.scalars().all()
    if not items:
        return SEED
    return [
        AlertOut(
            id=str(a.id), severity=a.severity, title=a.title, body=a.body,
            category=a.category, is_read=a.is_read, created_at=a.created_at,
        )
        for a in items
    ]


@router.post("/{alert_id}/dismiss")
async def dismiss(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> dict:
    try:
        aid = uuid.UUID(alert_id)
    except ValueError as e:
        raise HTTPException(400, "invalid alert_id") from e
    rows = await db.execute(
        select(Alert).where(Alert.id == aid, Alert.user_id == user.id)
    )
    alert = rows.scalars().first()
    if not alert:
        raise HTTPException(404, "alert not found")
    alert.is_read = True
    await db.commit()
    return {"ok": True}
