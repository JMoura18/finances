"""Daily price refresh.

Pulls latest close from Yahoo Finance for every Security in the DB and
upserts a row in `prices` for today.

Designed to be safe to call repeatedly: ON CONFLICT updates the close.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Price, Security


def _fetch_close(symbol: str) -> float | None:
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            return None
        return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        return None


async def refresh_prices(as_of: date | None = None) -> int:
    """Returns count of prices written. Cross-DB: select-then-insert/update."""
    today = as_of or date.today()
    written = 0

    async with SessionLocal() as db:
        rows = await db.execute(select(Security))
        securities = rows.scalars().all()

        for sec in securities:
            close = _fetch_close(sec.symbol)
            if close is None:
                continue

            existing = (await db.execute(
                select(Price).where(Price.security_id == sec.id, Price.as_of == today)
            )).scalars().first()

            if existing:
                existing.close = close
                existing.source = "yahoo"
            else:
                db.add(Price(
                    security_id=sec.id, as_of=today, close=close,
                    currency=sec.currency, source="yahoo",
                ))
            written += 1

        await db.commit()

    return written
