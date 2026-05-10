from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AccountOut(BaseModel):
    id: str
    name: str
    account_type: str
    institution: str | None
    currency: str
    market_value_cad: float
    book_value_cad: float


@router.get("", response_model=list[AccountOut])
async def list_accounts() -> list[AccountOut]:
    # Stub seed data so the UI renders before SnapTrade / DB are wired.
    return [
        AccountOut(
            id="acc-tfsa",
            name="TFSA",
            account_type="tfsa",
            institution="Wealthsimple",
            currency="CAD",
            market_value_cad=68420.13,
            book_value_cad=54200.00,
        ),
        AccountOut(
            id="acc-rrsp",
            name="RRSP",
            account_type="rrsp",
            institution="Questrade",
            currency="CAD",
            market_value_cad=124850.40,
            book_value_cad=110500.00,
        ),
        AccountOut(
            id="acc-fhsa",
            name="FHSA",
            account_type="fhsa",
            institution="Wealthsimple",
            currency="CAD",
            market_value_cad=16320.11,
            book_value_cad=15000.00,
        ),
        AccountOut(
            id="acc-non-reg",
            name="Margin",
            account_type="non_reg",
            institution="Questrade",
            currency="CAD",
            market_value_cad=42180.00,
            book_value_cad=38900.00,
        ),
    ]
