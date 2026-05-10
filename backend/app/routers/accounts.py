from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.database import get_db
from app.models import Account, Holding, Price

router = APIRouter()


class AccountOut(BaseModel):
    id: str
    name: str
    account_type: str
    institution: str | None
    currency: str
    market_value_cad: float
    book_value_cad: float


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    account_type: str
    institution: str | None = None
    currency: str = "CAD"


# Stub fallback when the DB is empty (dev convenience).
SEED = [
    AccountOut(id="acc-tfsa", name="TFSA", account_type="tfsa",
               institution="Wealthsimple", currency="CAD",
               market_value_cad=68420.13, book_value_cad=54200.0),
    AccountOut(id="acc-rrsp", name="RRSP", account_type="rrsp",
               institution="Questrade", currency="CAD",
               market_value_cad=124850.40, book_value_cad=110500.0),
    AccountOut(id="acc-fhsa", name="FHSA", account_type="fhsa",
               institution="Wealthsimple", currency="CAD",
               market_value_cad=16320.11, book_value_cad=15000.0),
    AccountOut(id="acc-non-reg", name="Margin", account_type="non_reg",
               institution="Questrade", currency="CAD",
               market_value_cad=42180.0, book_value_cad=38900.0),
]


async def _value_account(db: AsyncSession, account_id: uuid.UUID) -> tuple[float, float]:
    rows = await db.execute(
        select(Holding, Price.close)
        .join(Price, Price.security_id == Holding.security_id, isouter=True)
        .where(Holding.account_id == account_id)
    )
    market = Decimal(0)
    book = Decimal(0)
    seen: dict[uuid.UUID, tuple[Decimal, Decimal | None]] = {}
    for holding, close in rows.all():
        prev = seen.get(holding.id)
        if prev is None:
            seen[holding.id] = (holding.quantity, close)
            book += holding.acb_total_cad
            if close is not None:
                market += holding.quantity * close
        else:
            # newer Price already considered via DB ordering — ignore older
            pass
    return float(market), float(book)


@router.get("", response_model=list[AccountOut])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[AccountOut]:
    rows = await db.execute(select(Account).where(Account.user_id == user.id))
    accounts = rows.scalars().all()
    if not accounts:
        return SEED
    out: list[AccountOut] = []
    for a in accounts:
        market, book = await _value_account(db, a.id)
        out.append(AccountOut(
            id=str(a.id), name=a.name, account_type=a.account_type,
            institution=a.institution, currency=a.currency,
            market_value_cad=market, book_value_cad=book,
        ))
    return out


@router.post("", response_model=AccountOut, status_code=201)
async def create_account(
    payload: AccountCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> AccountOut:
    if payload.account_type not in {
        "tfsa", "rrsp", "fhsa", "non_reg", "rrif", "lira", "resp", "corporate",
    }:
        raise HTTPException(400, f"invalid account_type {payload.account_type!r}")
    a = Account(
        user_id=user.id,
        name=payload.name,
        account_type=payload.account_type,
        currency=payload.currency,
        institution=payload.institution,
        is_synced=False,
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return AccountOut(
        id=str(a.id), name=a.name, account_type=a.account_type,
        institution=a.institution, currency=a.currency,
        market_value_cad=0.0, book_value_cad=0.0,
    )
