from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.database import get_db
from app.models import Account, Holding, Security, Transaction
from app.services.csv_import import parse_csv
from app.services.portfolio import TxnInput, derive_holdings

router = APIRouter()


class TransactionOut(BaseModel):
    id: str
    account_id: str
    symbol: str | None
    txn_type: str
    quantity: float | None
    price: float | None
    amount_cad: float
    occurred_at: datetime
    notes: str | None = None


class TransactionCreate(BaseModel):
    account_id: str
    symbol: str | None = None
    txn_type: str
    quantity: float | None = None
    price: float | None = None
    amount_native: float = Field(ge=0)
    currency: str = "CAD"
    fx_rate: float = 1.0
    occurred_at: datetime
    notes: str | None = None


class CsvImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[dict[str, str]]


SEED = [
    TransactionOut(id="t1", account_id="acc-tfsa", symbol="VFV.TO",
                   txn_type="buy", quantity=20, price=131.10,
                   amount_cad=2622.00, occurred_at=datetime(2026, 4, 14, 14, 30)),
    TransactionOut(id="t2", account_id="acc-rrsp", symbol="MSFT",
                   txn_type="dividend", quantity=None, price=None,
                   amount_cad=42.80, occurred_at=datetime(2026, 4, 12, 9, 0)),
    TransactionOut(id="t3", account_id="acc-tfsa", symbol=None,
                   txn_type="contribution", quantity=None, price=None,
                   amount_cad=1500.00, occurred_at=datetime(2026, 4, 1, 9, 0)),
]


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[TransactionOut]:
    rows = await db.execute(
        select(Transaction, Account, Security)
        .join(Account, Account.id == Transaction.account_id)
        .join(Security, Security.id == Transaction.security_id, isouter=True)
        .where(Account.user_id == user.id)
        .order_by(Transaction.occurred_at.desc())
        .limit(200)
    )
    out: list[TransactionOut] = []
    for txn, _acc, sec in rows.all():
        out.append(TransactionOut(
            id=str(txn.id),
            account_id=str(txn.account_id),
            symbol=sec.symbol if sec else None,
            txn_type=txn.txn_type,
            quantity=float(txn.quantity) if txn.quantity is not None else None,
            price=float(txn.price) if txn.price is not None else None,
            amount_cad=float(txn.amount_cad),
            occurred_at=txn.occurred_at,
            notes=txn.notes,
        ))
    return out or SEED


async def _resolve_security(db: AsyncSession, symbol: str | None) -> Security | None:
    if not symbol:
        return None
    sym = symbol.upper()
    rows = await db.execute(select(Security).where(Security.symbol == sym))
    sec = rows.scalars().first()
    if sec:
        return sec
    # Auto-create unknown symbols as a CAD equity. Real implementation would
    # look up exchange/asset_class via a market data provider.
    sec = Security(symbol=sym, exchange="UNKNOWN", asset_class="equity",
                   currency="CAD", name=sym)
    db.add(sec)
    await db.flush()
    return sec


async def _recompute_account_holdings(db: AsyncSession, account_id: uuid.UUID) -> None:
    rows = await db.execute(
        select(Transaction).where(Transaction.account_id == account_id)
    )
    txns = rows.scalars().all()
    inputs = [
        TxnInput(
            account_id=t.account_id,
            security_id=t.security_id,
            txn_type=t.txn_type,
            quantity=t.quantity,
            amount_cad=t.amount_cad,
            occurred_at_iso=t.occurred_at.isoformat(),
        )
        for t in txns
    ]
    derived = derive_holdings(inputs)

    existing = await db.execute(
        select(Holding).where(Holding.account_id == account_id)
    )
    existing_by_sec = {h.security_id: h for h in existing.scalars().all()}

    derived_by_sec = {h.security_id: h for h in derived}
    for sec_id, h in derived_by_sec.items():
        cur = existing_by_sec.get(sec_id)
        if cur:
            cur.quantity = h.quantity
            cur.acb_total_cad = h.acb_total_cad
        else:
            db.add(Holding(
                account_id=account_id, security_id=sec_id,
                quantity=h.quantity, acb_total_cad=h.acb_total_cad,
            ))
    for sec_id, cur in existing_by_sec.items():
        if sec_id not in derived_by_sec:
            await db.delete(cur)


@router.post("", response_model=TransactionOut, status_code=201)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> TransactionOut:
    try:
        account_uuid = uuid.UUID(payload.account_id)
    except ValueError as e:
        raise HTTPException(400, "invalid account_id") from e

    acc_rows = await db.execute(
        select(Account).where(Account.id == account_uuid, Account.user_id == user.id)
    )
    account = acc_rows.scalars().first()
    if not account:
        raise HTTPException(404, "account not found")

    sec = await _resolve_security(db, payload.symbol)
    amount_cad = Decimal(str(payload.amount_native)) * Decimal(str(payload.fx_rate))

    txn = Transaction(
        account_id=account.id,
        security_id=sec.id if sec else None,
        txn_type=payload.txn_type,
        quantity=Decimal(str(payload.quantity)) if payload.quantity is not None else None,
        price=Decimal(str(payload.price)) if payload.price is not None else None,
        amount_native=Decimal(str(payload.amount_native)),
        currency=payload.currency,
        fx_rate=Decimal(str(payload.fx_rate)),
        amount_cad=amount_cad,
        occurred_at=payload.occurred_at,
        notes=payload.notes,
        source="manual",
    )
    db.add(txn)
    await db.flush()
    await _recompute_account_holdings(db, account.id)
    await db.commit()
    await db.refresh(txn)

    return TransactionOut(
        id=str(txn.id),
        account_id=str(txn.account_id),
        symbol=sec.symbol if sec else None,
        txn_type=txn.txn_type,
        quantity=float(txn.quantity) if txn.quantity is not None else None,
        price=float(txn.price) if txn.price is not None else None,
        amount_cad=float(txn.amount_cad),
        occurred_at=txn.occurred_at,
        notes=txn.notes,
    )


@router.post("/import-csv", response_model=CsvImportResult)
async def import_csv(
    account_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> CsvImportResult:
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError as e:
        raise HTTPException(400, "invalid account_id") from e
    acc_rows = await db.execute(
        select(Account).where(Account.id == account_uuid, Account.user_id == user.id)
    )
    account = acc_rows.scalars().first()
    if not account:
        raise HTTPException(404, "account not found")

    raw = (await file.read()).decode("utf-8", errors="replace")
    parsed = parse_csv(raw)
    imported = 0
    for row in parsed.parsed:
        sec = await _resolve_security(db, row.symbol)
        db.add(Transaction(
            account_id=account.id,
            security_id=sec.id if sec else None,
            txn_type=row.txn_type,
            quantity=row.quantity,
            price=row.price,
            amount_native=row.amount_native,
            currency=row.currency,
            fx_rate=row.fx_rate,
            amount_cad=row.amount_cad,
            occurred_at=row.occurred_at,
            notes=row.notes,
            source="csv",
        ))
        imported += 1
    await db.flush()
    await _recompute_account_holdings(db, account.id)
    await db.commit()
    return CsvImportResult(
        imported=imported,
        skipped=len(parsed.errors),
        errors=parsed.errors,
    )
