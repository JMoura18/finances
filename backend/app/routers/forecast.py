from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.agent_forecaster import run_forecaster_agent, serialize_results
from app.services.forecast_engine import ForecastInputs, run_forecast

router = APIRouter()


class ForecastRequest(BaseModel):
    scenario_name: str = Field(min_length=1, max_length=80)
    starting_balance_cad: float = Field(ge=0)
    annual_contribution_cad: float = Field(ge=0)
    horizon_years: int = Field(ge=1, le=60)
    equity_weight: float = Field(ge=0, le=1, default=0.7)
    target_cad: float | None = Field(default=None, ge=0)
    seed: int = 42
    n_simulations: int = Field(default=5000, ge=500, le=50000)


class ForecastResponse(BaseModel):
    inputs: dict[str, Any]
    results: dict[str, Any]
    narrative: dict[str, Any] | None = None


@router.post("", response_model=ForecastResponse)
async def create_forecast(payload: ForecastRequest) -> ForecastResponse:
    inputs = ForecastInputs(
        starting_balance_cad=payload.starting_balance_cad,
        annual_contribution_cad=payload.annual_contribution_cad,
        horizon_years=payload.horizon_years,
        equity_weight=payload.equity_weight,
        bond_weight=round(1.0 - payload.equity_weight, 4),
        target_cad=payload.target_cad,
        seed=payload.seed,
        n_simulations=payload.n_simulations,
    )
    results = run_forecast(inputs)

    narrative = await run_forecaster_agent(
        results, payload.scenario_name, payload.horizon_years
    )

    return ForecastResponse(
        inputs=payload.model_dump(),
        results=serialize_results(results),
        narrative=narrative,
    )
