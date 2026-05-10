from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

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


@router.get("", response_model=RiskResponse)
async def current_risk() -> RiskResponse:
    sample = [
        HoldingValuation("VFV.TO", "tech", "us", "etf", 23832.00),
        HoldingValuation("VEQT.TO", "diversified", "global", "etf", 16002.00),
        HoldingValuation("XEQT.TO", "diversified", "global", "etf", 19710.00),
        HoldingValuation("SHOP.TO", "tech", "ca", "equity", 9918.00),
        HoldingValuation("MSFT", "tech", "us", "equity", 27776.32),
        HoldingValuation("CNQ.TO", "energy", "ca", "equity", 10240.00),
        HoldingValuation("REI.UN.TO", "real_estate", "ca", "reit", 9700.00),
        HoldingValuation("ZAG.TO", "fixed_income", "ca", "etf", 11280.00),
    ]
    conc = score_concentration(sample)
    stresses = stress_test(sample)
    score = composite_score(conc, stresses)
    return RiskResponse(
        score=score,
        regime="normal",
        concentration=conc,
        stress_results=stresses,
    )
