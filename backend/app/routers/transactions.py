from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

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


@router.get("", response_model=list[TransactionOut])
async def list_transactions() -> list[TransactionOut]:
    return [
        TransactionOut(
            id="t1",
            account_id="acc-tfsa",
            symbol="VFV.TO",
            txn_type="buy",
            quantity=20,
            price=131.10,
            amount_cad=2622.00,
            occurred_at=datetime(2026, 4, 14, 14, 30),
        ),
        TransactionOut(
            id="t2",
            account_id="acc-rrsp",
            symbol="MSFT",
            txn_type="dividend",
            quantity=None,
            price=None,
            amount_cad=42.80,
            occurred_at=datetime(2026, 4, 12, 9, 0),
        ),
        TransactionOut(
            id="t3",
            account_id="acc-tfsa",
            symbol=None,
            txn_type="contribution",
            quantity=None,
            price=None,
            amount_cad=1500.00,
            occurred_at=datetime(2026, 4, 1, 9, 0),
        ),
    ]
