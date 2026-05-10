from datetime import datetime, timedelta, timezone

from app.services.calibration import evaluate_forecast, hit_rate


def test_inside_band_marked_in():
    created = datetime.now(timezone.utc) - timedelta(days=400)
    obs = evaluate_forecast(
        forecast_id="f-1", scenario_name="Test", horizon_years=10,
        forecast_results={
            "percentiles": {
                "p10": [100, 120, 140],
                "p50": [100, 130, 160],
                "p90": [100, 145, 200],
            },
        },
        forecast_created_at=created,
        observed_cad=135,
    )
    assert obs.in_p10_p90 is True


def test_outside_band_marked_out():
    created = datetime.now(timezone.utc) - timedelta(days=400)
    obs = evaluate_forecast(
        forecast_id="f-2", scenario_name="Test", horizon_years=10,
        forecast_results={
            "percentiles": {
                "p10": [100, 120, 140],
                "p50": [100, 130, 160],
                "p90": [100, 145, 200],
            },
        },
        forecast_created_at=created,
        observed_cad=300,
    )
    assert obs.in_p10_p90 is False


def test_hit_rate():
    class O:
        def __init__(self, in_band: bool):
            self.in_p10_p90 = in_band
    obs = [O(True), O(True), O(False), O(True)]
    assert abs(hit_rate(obs) - 0.75) < 1e-6  # type: ignore[arg-type]
