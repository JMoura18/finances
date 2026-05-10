from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.database import get_db
from app.models import Account, AgentRun, Holding, Price, Security
from app.services.agent_holding_researcher import run_holding_researcher
from app.services.market_data import (
    fetch_earnings,
    fetch_fundamentals,
    fetch_news,
)
from app.services.news_ranker import rank_headlines

router = APIRouter()


class HoldingOut(BaseModel):
    id: str
    account_id: str
    symbol: str
    name: str
    asset_class: str
    sector: str | None
    region: str | None
    quantity: float
    last_price_cad: float
    market_value_cad: float
    acb_total_cad: float
    unrealized_pnl_cad: float
    weight: float


SEED = [
    ("h-vfv", "acc-tfsa", "VFV.TO", "Vanguard S&P 500", "etf", "diversified", "us", 180, 132.40, 23832.00, 18900.00),
    ("h-veqt", "acc-rrsp", "VEQT.TO", "Vanguard All-Equity ETF", "etf", "diversified", "global", 420, 38.10, 16002.00, 14700.00),
    ("h-xeqt", "acc-tfsa", "XEQT.TO", "iShares All-Equity ETF", "etf", "diversified", "global", 600, 32.85, 19710.00, 17800.00),
    ("h-shop", "acc-non-reg", "SHOP.TO", "Shopify", "equity", "tech", "ca", 90, 110.20, 9918.00, 7200.00),
    ("h-msft", "acc-rrsp", "MSFT", "Microsoft", "equity", "tech", "us", 40, 510.30, 27776.32, 21200.00),
    ("h-cnq", "acc-non-reg", "CNQ.TO", "Canadian Natural Resources", "equity", "energy", "ca", 200, 51.20, 10240.00, 9100.00),
    ("h-rein", "acc-tfsa", "REI.UN.TO", "RioCan REIT", "reit", "real_estate", "ca", 500, 19.40, 9700.00, 11200.00),
    ("h-bnd", "acc-rrsp", "ZAG.TO", "BMO Aggregate Bond ETF", "etf", "fixed_income", "ca", 800, 14.10, 11280.00, 12100.00),
]


def _seed() -> list[HoldingOut]:
    total = sum(r[9] for r in SEED)
    out: list[HoldingOut] = []
    for r in SEED:
        (id_, acc, sym, name, cls, sector, region, qty, px, mv, acb) = r
        out.append(HoldingOut(
            id=id_, account_id=acc, symbol=sym, name=name, asset_class=cls,
            sector=sector, region=region, quantity=float(qty),
            last_price_cad=float(px), market_value_cad=float(mv),
            acb_total_cad=float(acb), unrealized_pnl_cad=float(mv - acb),
            weight=float(mv / total) if total else 0.0,
        ))
    return out


@router.get("", response_model=list[HoldingOut])
async def list_holdings(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[HoldingOut]:
    rows = await db.execute(
        select(Holding, Account, Security, Price.close)
        .join(Account, Account.id == Holding.account_id)
        .join(Security, Security.id == Holding.security_id)
        .join(Price, Price.security_id == Holding.security_id, isouter=True)
        .where(Account.user_id == user.id)
        .order_by(Price.as_of.desc().nullslast())
    )
    seen: dict[str, HoldingOut] = {}
    market_by_id: dict[str, Decimal] = {}
    total = Decimal(0)
    for holding, _acc, security, close in rows.all():
        if str(holding.id) in seen:
            continue
        px = Decimal(close) if close is not None else Decimal(0)
        market = holding.quantity * px
        total += market
        market_by_id[str(holding.id)] = market
        seen[str(holding.id)] = HoldingOut(
            id=str(holding.id),
            account_id=str(holding.account_id),
            symbol=security.symbol,
            name=security.name or security.symbol,
            asset_class=security.asset_class,
            sector=security.sector,
            region=security.region,
            quantity=float(holding.quantity),
            last_price_cad=float(px),
            market_value_cad=float(market),
            acb_total_cad=float(holding.acb_total_cad),
            unrealized_pnl_cad=float(market - holding.acb_total_cad),
            weight=0.0,
        )

    if not seen:
        return _seed()

    if total > 0:
        for hid, h in seen.items():
            h.weight = float(market_by_id[hid] / total)
    return list(seen.values())


@router.get("/{holding_id}", response_model=HoldingOut)
async def get_holding(
    holding_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> HoldingOut:
    holdings = await list_holdings(db, user)
    for h in holdings:
        if h.id == holding_id:
            return h
    raise HTTPException(404, "holding not found")


class HoldingResearchResponse(BaseModel):
    symbol: str
    narrative: str
    fundamentals: dict


class NewsItemOut(BaseModel):
    id: str
    headline: str
    url: str
    published_at: str | None
    source: str
    relevance: float | None
    sentiment: float | None
    summary: str | None = None


class EarningsResponse(BaseModel):
    symbol: str
    next_date: datetime | None
    last_date: datetime | None
    consensus_eps: float | None
    reported_eps: float | None


async def _holding_or_404(
    db: AsyncSession, user: CurrentUser, holding_id: str,
) -> HoldingOut:
    holdings = await list_holdings(db, user)
    for h in holdings:
        if h.id == holding_id:
            return h
    raise HTTPException(404, "holding not found")


@router.get("/{holding_id}/research", response_model=HoldingResearchResponse)
async def research(
    holding_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> HoldingResearchResponse:
    h = await _holding_or_404(db, user, holding_id)
    fund = fetch_fundamentals(h.symbol)
    raw = fetch_news(h.symbol, limit=8)
    ranked = rank_headlines(raw, symbol=h.symbol, name=h.name, sector=h.sector)
    dossier = {
        "symbol": h.symbol,
        "name": h.name,
        "sector": h.sector,
        "region": h.region,
        "fundamentals": {
            "market_cap": fund.market_cap,
            "pe_ratio": fund.pe_ratio,
            "dividend_yield": fund.dividend_yield,
            "fifty_two_week_high": fund.fifty_two_week_high,
            "fifty_two_week_low": fund.fifty_two_week_low,
            "beta": fund.beta,
        },
        "top_headlines": [
            {"headline": r.headline, "relevance": r.relevance, "sentiment": r.sentiment}
            for r in ranked[:5]
        ],
    }
    result = await run_holding_researcher(dossier)
    db.add(AgentRun(
        user_id=user.id,
        agent_name="holding_researcher",
        model=result["model"],
        input_payload=result["input_payload"],
        output_text=result["output_text"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        duration_ms=result["duration_ms"],
    ))
    await db.commit()
    return HoldingResearchResponse(
        symbol=h.symbol,
        narrative=result["output_text"],
        fundamentals=dossier["fundamentals"],
    )


@router.get("/{holding_id}/news", response_model=list[NewsItemOut])
async def holding_news(
    holding_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[NewsItemOut]:
    h = await _holding_or_404(db, user, holding_id)
    raw = fetch_news(h.symbol, limit=20)
    ranked = rank_headlines(raw, symbol=h.symbol, name=h.name, sector=h.sector)
    out: list[NewsItemOut] = []
    for i, r in enumerate(ranked):
        match = next((x for x in raw if x.get("headline") == r.headline), {})
        out.append(NewsItemOut(
            id=f"news-{i}",
            headline=r.headline,
            url=r.url,
            published_at=match.get("published_at"),
            source=r.source,
            relevance=r.relevance,
            sentiment=r.sentiment,
        ))
    return out


@router.get("/{holding_id}/earnings", response_model=EarningsResponse)
async def holding_earnings(
    holding_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> EarningsResponse:
    h = await _holding_or_404(db, user, holding_id)
    e = fetch_earnings(h.symbol)
    return EarningsResponse(
        symbol=h.symbol,
        next_date=e.next_date,
        last_date=e.last_date,
        consensus_eps=e.consensus_eps,
        reported_eps=e.reported_eps,
    )
