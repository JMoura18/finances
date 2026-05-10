from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.database import get_db
from app.models import Forecast

router = APIRouter()


class CalibrationOut(BaseModel):
    forecast_id: str
    scenario_name: str
    horizon_years: int
    median_predicted_cad: float
    observed_cad: float
    pct_error: float
    in_p10_p90: bool
    generated_at: datetime


SEED = [
    CalibrationOut(
        forecast_id="seed-1", scenario_name="Base case 2024",
        horizon_years=25, median_predicted_cad=300_000,
        observed_cad=312_400, pct_error=0.041, in_p10_p90=True,
        generated_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    ),
    CalibrationOut(
        forecast_id="seed-2", scenario_name="Conservative 2025",
        horizon_years=25, median_predicted_cad=280_000,
        observed_cad=270_120, pct_error=-0.035, in_p10_p90=True,
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ),
]


@router.get("", response_model=list[CalibrationOut])
async def list_calibrations(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[CalibrationOut]:
    rows = await db.execute(
        select(Forecast)
        .where(Forecast.user_id == user.id)
        .order_by(Forecast.created_at.desc())
        .limit(20)
    )
    items = rows.scalars().all()
    if not items:
        return SEED

    out: list[CalibrationOut] = []
    for f in items:
        cal = (f.results or {}).get("calibration")
        if not cal:
            continue
        out.append(CalibrationOut(
            forecast_id=str(f.id),
            scenario_name=f.scenario_name,
            horizon_years=f.horizon_years,
            median_predicted_cad=float(cal["median_predicted_cad"]),
            observed_cad=float(cal["observed_cad"]),
            pct_error=float(cal["pct_error"]),
            in_p10_p90=bool(cal["in_p10_p90"]),
            generated_at=f.created_at,
        ))
    return out or SEED
