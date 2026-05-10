"""Bootstrap a dev database with a fixed user, accounts, securities,
transactions, and a starter price set.

Idempotent: skips inserts when the dev user already exists.

Run: python -m scripts.seed_dev
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.auth import DEV_USER
from app.database import Base, SessionLocal, engine
from app.models import (
    Account,
    ContributionRoom,
    Holding,
    Price,
    Security,
    Transaction,
    User,
)
from app.services.portfolio import TxnInput, derive_holdings


SECURITY_SEED = [
    ("VFV.TO", "TSX", "etf", "CAD", "Vanguard S&P 500", "diversified", "us"),
    ("VEQT.TO", "TSX", "etf", "CAD", "Vanguard All-Equity ETF", "diversified", "global"),
    ("XEQT.TO", "TSX", "etf", "CAD", "iShares All-Equity ETF", "diversified", "global"),
    ("ZAG.TO", "TSX", "etf", "CAD", "BMO Aggregate Bond ETF", "fixed_income", "ca"),
    ("REI.UN.TO", "TSX", "reit", "CAD", "RioCan REIT", "real_estate", "ca"),
    ("SHOP.TO", "TSX", "equity", "CAD", "Shopify", "tech", "ca"),
    ("CNQ.TO", "TSX", "equity", "CAD", "Canadian Natural Resources", "energy", "ca"),
    ("MSFT", "NASDAQ", "equity", "USD", "Microsoft", "tech", "us"),
]

ACCOUNT_SEED = [
    ("TFSA", "tfsa", "Wealthsimple"),
    ("RRSP", "rrsp", "Questrade"),
    ("FHSA", "fhsa", "Wealthsimple"),
    ("Margin", "non_reg", "Questrade"),
]

PRICE_SEED: dict[str, Decimal] = {
    "VFV.TO": Decimal("132.40"),
    "VEQT.TO": Decimal("38.10"),
    "XEQT.TO": Decimal("32.85"),
    "ZAG.TO": Decimal("14.10"),
    "REI.UN.TO": Decimal("19.40"),
    "SHOP.TO": Decimal("110.20"),
    "CNQ.TO": Decimal("51.20"),
    "MSFT": Decimal("510.30"),
}

# (account_label, symbol, txn_type, qty, amount_cad, days_ago)
TXNS_SEED = [
    ("TFSA", "VFV.TO", "buy", Decimal("100"), Decimal("12000"), 720),
    ("TFSA", "VFV.TO", "buy", Decimal("80"), Decimal("9800"), 280),
    ("TFSA", "XEQT.TO", "buy", Decimal("600"), Decimal("17800"), 360),
    ("TFSA", "REI.UN.TO", "buy", Decimal("500"), Decimal("11200"), 450),
    ("RRSP", "VEQT.TO", "buy", Decimal("420"), Decimal("14700"), 540),
    ("RRSP", "MSFT", "buy", Decimal("40"), Decimal("21200"), 600),
    ("RRSP", "ZAG.TO", "buy", Decimal("800"), Decimal("12100"), 380),
    ("Margin", "SHOP.TO", "buy", Decimal("90"), Decimal("7200"), 200),
    ("Margin", "CNQ.TO", "buy", Decimal("200"), Decimal("9100"), 250),
    ("TFSA", None, "contribution", None, Decimal("1500"), 38),
    ("RRSP", "MSFT", "dividend", None, Decimal("42.80"), 28),
]

ROOM_SEED = [
    ("tfsa", 2026, Decimal("102000"), Decimal("68420")),
    ("rrsp", 2026, Decimal("88000"), Decimal("62400")),
    ("fhsa", 2026, Decimal("32000"), Decimal("16320")),
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        existing = await db.execute(
            select(User).where(User.firebase_uid == DEV_USER.firebase_uid)
        )
        if existing.scalar_one_or_none():
            print("dev user already seeded")
            return

        user = User(
            id=DEV_USER.id,
            firebase_uid=DEV_USER.firebase_uid,
            email=DEV_USER.email,
            display_name="Jesse (dev)",
            province="ON",
            birth_year=1991,
        )
        db.add(user)

        sec_by_symbol: dict[str, Security] = {}
        for sym, exch, cls, ccy, name, sector, region in SECURITY_SEED:
            s = Security(
                symbol=sym, exchange=exch, asset_class=cls, currency=ccy,
                name=name, sector=sector, region=region,
            )
            db.add(s)
            sec_by_symbol[sym] = s

        await db.flush()

        acc_by_label: dict[str, Account] = {}
        for name, kind, inst in ACCOUNT_SEED:
            a = Account(
                user_id=user.id,
                name=name,
                account_type=kind,
                currency="CAD",
                institution=inst,
                is_synced=False,
            )
            db.add(a)
            acc_by_label[name] = a
        await db.flush()

        today = datetime.now(timezone.utc)
        txn_inputs: list[TxnInput] = []

        for acc_label, sym, kind, qty, amt, days_ago in TXNS_SEED:
            acc = acc_by_label[acc_label]
            sec = sec_by_symbol.get(sym) if sym else None
            occurred = today.replace(hour=14, minute=30) - _days(days_ago)
            t = Transaction(
                account_id=acc.id,
                security_id=sec.id if sec else None,
                txn_type=kind,
                quantity=qty,
                price=(amt / qty) if (qty and qty != 0) else None,
                amount_native=amt,
                currency="CAD",
                fx_rate=Decimal("1"),
                amount_cad=amt,
                occurred_at=occurred,
                source="manual",
            )
            db.add(t)
            if sec is not None:
                txn_inputs.append(
                    TxnInput(
                        account_id=acc.id,
                        security_id=sec.id,
                        txn_type=kind,
                        quantity=qty,
                        amount_cad=amt,
                        occurred_at_iso=occurred.isoformat(),
                    )
                )

        for sym, px in PRICE_SEED.items():
            sec = sec_by_symbol[sym]
            db.add(Price(security_id=sec.id, as_of=date.today(), close=px,
                         currency=sec.currency, source="seed"))

        for kind, year, total, used in ROOM_SEED:
            db.add(ContributionRoom(
                user_id=user.id, account_type=kind, tax_year=year,
                total_room_cad=total, used_cad=used,
            ))

        # Persist holdings derived from transactions
        for h in derive_holdings(txn_inputs):
            db.add(Holding(
                account_id=h.account_id,
                security_id=h.security_id,
                quantity=h.quantity,
                acb_total_cad=h.acb_total_cad,
            ))

        await db.commit()
        print(f"seeded user {user.email} with {len(SECURITY_SEED)} securities, "
              f"{len(ACCOUNT_SEED)} accounts, {len(TXNS_SEED)} transactions")


def _days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
