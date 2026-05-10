from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.database import get_db
from app.models import Account, ContributionRoom, Holding, Price, Security
from app.services.asset_location import HoldingPlacement, recommend_placement

router = APIRouter()


class RoomOut(BaseModel):
    account_type: str
    tax_year: int
    total_room_cad: float
    used_cad: float
    available_cad: float


class AssetLocationOut(BaseModel):
    symbol: str
    current_account_type: str
    recommended_account_type: str
    reason: str


SEED_ROOMS = [
    RoomOut(account_type="tfsa", tax_year=2026, total_room_cad=102000.0,
            used_cad=68420.0, available_cad=33580.0),
    RoomOut(account_type="rrsp", tax_year=2026, total_room_cad=88000.0,
            used_cad=62400.0, available_cad=25600.0),
    RoomOut(account_type="fhsa", tax_year=2026, total_room_cad=32000.0,
            used_cad=16320.0, available_cad=15680.0),
]


@router.get("/rooms", response_model=list[RoomOut])
async def contribution_rooms(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[RoomOut]:
    rows = await db.execute(
        select(ContributionRoom).where(ContributionRoom.user_id == user.id)
    )
    items = rows.scalars().all()
    if not items:
        return SEED_ROOMS
    return [
        RoomOut(
            account_type=r.account_type,
            tax_year=r.tax_year,
            total_room_cad=float(r.total_room_cad),
            used_cad=float(r.used_cad),
            available_cad=float(r.total_room_cad - r.used_cad),
        )
        for r in items
    ]


@router.get("/asset-location", response_model=list[AssetLocationOut])
async def asset_location(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[AssetLocationOut]:
    rows = await db.execute(
        select(Holding, Account, Security, Price.close)
        .join(Account, Account.id == Holding.account_id)
        .join(Security, Security.id == Holding.security_id)
        .join(Price, Price.security_id == Holding.security_id, isouter=True)
        .where(Account.user_id == user.id)
    )
    seen: set = set()
    placements: list[HoldingPlacement] = []
    for h, acc, sec, _close in rows.all():
        if h.id in seen:
            continue
        seen.add(h.id)
        placements.append(HoldingPlacement(
            symbol=sec.symbol,
            asset_class=sec.asset_class,
            sector=sec.sector,
            region=sec.region,
            is_dividend_payer=sec.asset_class in {"equity", "etf", "reit"},
            current_account_type=acc.account_type,
        ))

    if not placements:
        # Seed example: one suggestion that demonstrates the shape
        return [
            AssetLocationOut(
                symbol="MSFT",
                current_account_type="non_reg",
                recommended_account_type="rrsp",
                reason="US dividends in an RRSP avoid the 15% withholding tax under the Canada–US treaty.",
            ),
        ]

    return [
        AssetLocationOut(
            symbol=s.symbol,
            current_account_type=s.current_account_type,
            recommended_account_type=s.recommended_account_type,
            reason=s.reason,
        )
        for s in recommend_placement(placements)
    ]


# Compute used room from transactions for any year
async def used_room_cad(
    db: AsyncSession, user_id, account_type: str, tax_year: int
) -> Decimal:
    rows = await db.execute(
        select(Account).where(
            Account.user_id == user_id, Account.account_type == account_type,
        )
    )
    _ = rows.scalars().all()
    # Implementation note: aggregate `contribution` and `withdrawal` transactions
    # by year, net them. Left as a follow-up — current SEED_ROOMS handles dev.
    return Decimal(0)
