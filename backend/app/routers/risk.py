from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.database import get_db
from app.models import Account, AgentRun, Holding, Price, RiskSnapshot, Security
from app.services.agent_risk_analyst import run_risk_analyst_agent
from app.services.risk_scorer import (
    HoldingValuation,
    composite_score,
    score_concentration,
    stress_test,
)

router = APIRouter()


class RiskResponse(BaseModel):
    score: float
    regime: str
    concentration: dict
    stress_results: dict


SAMPLE = [
    HoldingValuation("VFV.TO", "diversified", "us", "etf", 23832.00),
    HoldingValuation("VEQT.TO", "diversified", "global", "etf", 16002.00),
    HoldingValuation("XEQT.TO", "diversified", "global", "etf", 19710.00),
    HoldingValuation("SHOP.TO", "tech", "ca", "equity", 9918.00),
    HoldingValuation("MSFT", "tech", "us", "equity", 27776.32),
    HoldingValuation("CNQ.TO", "energy", "ca", "equity", 10240.00),
    HoldingValuation("REI.UN.TO", "real_estate", "ca", "reit", 9700.00),
    HoldingValuation("ZAG.TO", "fixed_income", "ca", "etf", 11280.00),
]


async def _user_holdings(db: AsyncSession, user_id) -> list[HoldingValuation]:
    rows = await db.execute(
        select(Holding, Security, Price.close)
        .join(Account, Account.id == Holding.account_id)
        .join(Security, Security.id == Holding.security_id)
        .join(Price, Price.security_id == Holding.security_id, isouter=True)
        .where(Account.user_id == user_id)
        .order_by(Price.as_of.desc().nullslast())
    )
    seen: set = set()
    out: list[HoldingValuation] = []
    for h, sec, close in rows.all():
        if h.id in seen:
            continue
        seen.add(h.id)
        px = Decimal(close) if close is not None else Decimal(0)
        out.append(HoldingValuation(
            symbol=sec.symbol, sector=sec.sector, region=sec.region,
            asset_class=sec.asset_class, market_value_cad=float(h.quantity * px),
        ))
    return out


@router.get("", response_model=RiskResponse)
async def current_risk(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> RiskResponse:
    holdings = await _user_holdings(db, user.id) or SAMPLE
    conc = score_concentration(holdings)
    stresses = stress_test(holdings)
    score = composite_score(conc, stresses)
    return RiskResponse(score=score, regime="normal",
                        concentration=conc, stress_results=stresses)


@router.get("/snapshots")
async def snapshots(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[dict]:
    rows = await db.execute(
        select(RiskSnapshot)
        .where(RiskSnapshot.user_id == user.id)
        .order_by(RiskSnapshot.created_at.desc())
        .limit(26)
    )
    return [
        {
            "id": str(s.id),
            "score": float(s.score),
            "regime": s.regime,
            "created_at": s.created_at.isoformat(),
        }
        for s in rows.scalars().all()
    ]


@router.get("/narrative")
async def narrative(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> dict:
    holdings = await _user_holdings(db, user.id) or SAMPLE
    conc = score_concentration(holdings)
    stresses = stress_test(holdings)
    score = composite_score(conc, stresses)
    result = await run_risk_analyst_agent(score, "normal", conc, stresses)
    db.add(AgentRun(
        user_id=user.id,
        agent_name="risk_analyst",
        model=result["model"],
        input_payload=result["input_payload"],
        output_text=result["output_text"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        duration_ms=result["duration_ms"],
    ))
    await db.commit()
    return {"output_text": result["output_text"]}
