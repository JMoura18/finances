from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.config import get_settings
from app.database import get_db
from app.integrations.snaptrade import get_connect_url
from app.models import Account
from app.services.reconciliation import reconcile_user

router = APIRouter()


class StatusResponse(BaseModel):
    connected: bool
    brokerages: list[str]
    last_sync: datetime | None


class ConnectUrlResponse(BaseModel):
    url: str


class SyncResponse(BaseModel):
    ok: bool
    reconciled: int


@router.get("/status", response_model=StatusResponse)
async def status(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> StatusResponse:
    rows = await db.execute(
        select(Account).where(Account.user_id == user.id, Account.is_synced.is_(True))
    )
    synced = rows.scalars().all()
    brokerages = sorted({a.institution for a in synced if a.institution})
    s = get_settings()
    configured = bool(s.snaptrade_client_id and s.snaptrade_consumer_key)
    return StatusResponse(
        connected=bool(synced) or not configured,  # mock mode looks "connected"
        brokerages=brokerages,
        last_sync=None,
    )


@router.post("/connect-url", response_model=ConnectUrlResponse)
async def connect_url(user: CurrentUser = CurrentUserDep) -> ConnectUrlResponse:
    url = await get_connect_url(str(user.id))
    return ConnectUrlResponse(url=url)


@router.post("/sync", response_model=SyncResponse)
async def sync(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> SyncResponse:
    result = await reconcile_user(db, user.id, str(user.id))
    await db.commit()
    _ = datetime.now(timezone.utc)
    return SyncResponse(ok=True, reconciled=result.accounts_synced)
