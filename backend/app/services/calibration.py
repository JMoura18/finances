"""Forecast calibration.

Compares each historical Forecast against realized portfolio value at the
forecast horizon (or partial horizon if not yet matured).

Three diagnostics:
  - pct_error: (observed − median_predicted) / median_predicted
  - in_p10_p90: did the realized value land inside the modeled 80% band
  - cumulative observation count (so we can compute hit rate over time)

The output is observations only. We never auto-tune forecast parameters
based on this — the user (or a follow-up training pipeline) does.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class CalibrationObservation:
    forecast_id: str
    scenario_name: str
    horizon_years: int
    median_predicted_cad: float
    p10_predicted_cad: float
    p90_predicted_cad: float
    observed_cad: float
    pct_error: float
    in_p10_p90: bool
    elapsed_years: float


def evaluate_forecast(
    forecast_id: str,
    scenario_name: str,
    horizon_years: int,
    forecast_results: dict,
    forecast_created_at: datetime,
    observed_cad: float,
    now: datetime | None = None,
) -> CalibrationObservation:
    if now is None:
        now = datetime.now(timezone.utc)
    elapsed = max(0.0, (now - forecast_created_at).days / 365.25)
    elapsed_idx = min(int(round(elapsed)), horizon_years)

    pcts = forecast_results.get("percentiles", {})
    p10 = pcts.get("p10", [forecast_results.get("p10_terminal", 0.0)])[elapsed_idx]
    p50 = pcts.get("p50", [forecast_results.get("median_terminal", 0.0)])[elapsed_idx]
    p90 = pcts.get("p90", [forecast_results.get("p90_terminal", 0.0)])[elapsed_idx]

    pct_error = (observed_cad - p50) / p50 if p50 else 0.0
    in_band = bool(p10 <= observed_cad <= p90)

    return CalibrationObservation(
        forecast_id=forecast_id,
        scenario_name=scenario_name,
        horizon_years=horizon_years,
        median_predicted_cad=p50,
        p10_predicted_cad=p10,
        p90_predicted_cad=p90,
        observed_cad=observed_cad,
        pct_error=pct_error,
        in_p10_p90=in_band,
        elapsed_years=round(elapsed, 2),
    )


def hit_rate(observations: list[CalibrationObservation]) -> float:
    if not observations:
        return 0.0
    inside = sum(1 for o in observations if o.in_p10_p90)
    return inside / len(observations)
