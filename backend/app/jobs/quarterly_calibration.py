"""Quarterly calibration job.

For every Forecast in the DB, compute observed portfolio value as of now,
and write a calibration record (kept inside the existing forecasts.results
JSON to avoid a new table). Idempotent — overwrites the calibration block.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.models import Account, Forecast, Holding, Price, User
from app.services.calibration import evaluate_forecast


async def _user_value_cad(db: AsyncSession, user_id: uuid.UUID) -> float:
    rows = await db.execute(
        select(Holding, Price.close)
        .join(Account, Account.id == Holding.account_id)
        .join(Price, Price.security_id == Holding.security_id, isouter=True)
        .where(Account.user_id == user_id)
        .order_by(Price.as_of.desc().nullslast())
    )
    seen: set = set()
    total = Decimal(0)
    for h, close in rows.all():
        if h.id in seen:
            continue
        seen.add(h.id)
        if close is not None:
            total += h.quantity * close
    return float(total)


async def calibrate_all() -> int:
    written = 0
    async with SessionLocal() as db:
        users = (await db.execute(select(User))).scalars().all()
        for user in users:
            observed = await _user_value_cad(db, user.id)
            forecasts = (
                await db.execute(select(Forecast).where(Forecast.user_id == user.id))
            ).scalars().all()
            for f in forecasts:
                obs = evaluate_forecast(
                    forecast_id=str(f.id),
                    scenario_name=f.scenario_name,
                    horizon_years=f.horizon_years,
                    forecast_results=dict(f.results),
                    forecast_created_at=f.created_at,
                    observed_cad=observed,
                )
                results = dict(f.results)
                results["calibration"] = {
                    "median_predicted_cad": obs.median_predicted_cad,
                    "p10_predicted_cad": obs.p10_predicted_cad,
                    "p90_predicted_cad": obs.p90_predicted_cad,
                    "observed_cad": obs.observed_cad,
                    "pct_error": obs.pct_error,
                    "in_p10_p90": obs.in_p10_p90,
                    "elapsed_years": obs.elapsed_years,
                }
                f.results = results
                written += 1
        await db.commit()
    return written
