"""Portfolio risk scoring.

Outputs:
  - concentration: HHI-based score per holding, sector, and region
  - stress_results: portfolio drawdown under named historical shocks
  - composite score: 0-100, higher = riskier
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class HoldingValuation:
    symbol: str
    sector: str | None
    region: str | None
    asset_class: str
    market_value_cad: float


STRESS_SHOCKS: dict[str, dict[str, float]] = {
    "covid_2020": {"equity": -0.34, "bond": 0.05, "reit": -0.30, "crypto": -0.45, "cash": 0.0},
    "gfc_2008": {"equity": -0.50, "bond": 0.10, "reit": -0.65, "crypto": -0.70, "cash": 0.0},
    "rates_2022": {"equity": -0.20, "bond": -0.15, "reit": -0.25, "crypto": -0.65, "cash": 0.0},
}


def _hhi(weights: list[float]) -> float:
    return float(sum(w * w for w in weights))


def score_concentration(holdings: list[HoldingValuation]) -> dict[str, object]:
    total = sum(h.market_value_cad for h in holdings)
    if total <= 0:
        return {"hhi": 0.0, "by_sector": {}, "by_region": {}, "top": []}

    weights = [h.market_value_cad / total for h in holdings]
    hhi = _hhi(weights)

    sector_weights: dict[str, float] = defaultdict(float)
    region_weights: dict[str, float] = defaultdict(float)
    for h, w in zip(holdings, weights):
        sector_weights[h.sector or "unknown"] += w
        region_weights[h.region or "unknown"] += w

    top = sorted(
        [{"symbol": h.symbol, "weight": w} for h, w in zip(holdings, weights)],
        key=lambda x: x["weight"],
        reverse=True,
    )[:5]

    return {
        "hhi": hhi,
        "by_sector": dict(sector_weights),
        "by_region": dict(region_weights),
        "top": top,
    }


def stress_test(holdings: list[HoldingValuation]) -> dict[str, float]:
    total = sum(h.market_value_cad for h in holdings)
    if total <= 0:
        return {name: 0.0 for name in STRESS_SHOCKS}

    out: dict[str, float] = {}
    for name, shocks in STRESS_SHOCKS.items():
        shocked = 0.0
        for h in holdings:
            shock = shocks.get(h.asset_class, -0.10)
            shocked += h.market_value_cad * shock
        out[name] = shocked / total
    return out


def composite_score(
    concentration: dict[str, object], stresses: dict[str, float]
) -> float:
    hhi = float(concentration.get("hhi", 0.0))
    worst_drawdown = abs(min(stresses.values(), default=0.0))
    # 0..100 — HHI saturates at ~0.4, drawdown at 60%
    conc_pts = min(hhi / 0.4, 1.0) * 50.0
    stress_pts = min(worst_drawdown / 0.6, 1.0) * 50.0
    return round(conc_pts + stress_pts, 2)
