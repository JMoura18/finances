from app.services.forecast_engine import ForecastInputs, run_forecast


def test_forecast_is_deterministic():
    inputs = ForecastInputs(
        starting_balance_cad=100_000,
        annual_contribution_cad=10_000,
        horizon_years=20,
        seed=7,
    )
    a = run_forecast(inputs)
    b = run_forecast(inputs)
    assert a.median_terminal == b.median_terminal


def test_forecast_target_probability_in_range():
    inputs = ForecastInputs(
        starting_balance_cad=100_000,
        annual_contribution_cad=10_000,
        horizon_years=30,
        target_cad=1_000_000,
    )
    r = run_forecast(inputs)
    assert r.prob_hit_target is not None
    assert 0.0 <= r.prob_hit_target <= 1.0


def test_percentile_band_ordering():
    r = run_forecast(
        ForecastInputs(
            starting_balance_cad=50_000,
            annual_contribution_cad=5_000,
            horizon_years=25,
        )
    )
    last = -1
    assert r.percentiles["p10"][last] <= r.percentiles["p50"][last] <= r.percentiles["p90"][last]
