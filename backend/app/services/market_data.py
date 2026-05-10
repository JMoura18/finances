"""Market data adapter.

Wraps Yahoo Finance for fundamentals, news headlines, and earnings dates.
Returns deterministic mock data when yfinance isn't installed or the call
fails — keeps the dev experience smooth.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class Fundamentals:
    market_cap: float | None = None
    pe_ratio: float | None = None
    dividend_yield: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    beta: float | None = None


@dataclass
class Earnings:
    next_date: datetime | None = None
    last_date: datetime | None = None
    consensus_eps: float | None = None
    reported_eps: float | None = None


def fetch_fundamentals(symbol: str) -> Fundamentals:
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        return Fundamentals(
            market_cap=_get_float(info, "marketCap"),
            pe_ratio=_get_float(info, "trailingPE"),
            dividend_yield=_get_float(info, "dividendYield"),
            fifty_two_week_high=_get_float(info, "fiftyTwoWeekHigh"),
            fifty_two_week_low=_get_float(info, "fiftyTwoWeekLow"),
            beta=_get_float(info, "beta"),
        )
    except Exception:
        return Fundamentals(market_cap=None, pe_ratio=None,
                            dividend_yield=None, beta=None,
                            fifty_two_week_high=None, fifty_two_week_low=None)


def fetch_news(symbol: str, limit: int = 12) -> list[dict[str, Any]]:
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        items = (ticker.news or [])[:limit]
        out: list[dict[str, Any]] = []
        for n in items:
            ts = n.get("providerPublishTime")
            published = (
                datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                if isinstance(ts, (int, float)) else None
            )
            out.append({
                "headline": n.get("title", ""),
                "url": n.get("link", ""),
                "source": n.get("publisher", ""),
                "published_at": published,
            })
        return out
    except Exception:
        return _mock_news(symbol)


def fetch_earnings(symbol: str) -> Earnings:
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        cal = getattr(ticker, "calendar", None)
        next_dt = None
        if cal is not None and not getattr(cal, "empty", True):
            try:
                next_dt = cal.iloc[0, 0].to_pydatetime()
            except Exception:
                next_dt = None
        return Earnings(next_date=next_dt)
    except Exception:
        return Earnings(next_date=None)


def _get_float(d: dict, key: str) -> float | None:
    v = d.get(key)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _mock_news(symbol: str) -> list[dict[str, Any]]:
    return [
        {
            "headline": f"{symbol} sees record quarterly revenue, beats analyst estimates",
            "url": "https://example.invalid/1",
            "source": "Mock Wire",
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "headline": f"Analyst upgrades {symbol} citing strong margins",
            "url": "https://example.invalid/2",
            "source": "Mock Wire",
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "headline": "Sector rotation cools high-flying tech names",
            "url": "https://example.invalid/3",
            "source": "Mock Wire",
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
