"""Monte Carlo retirement forecast engine.

Deterministic given a seed. Returns percentile bands plus probability of
hitting a target. Numbers stay in CAD; equity vs bond split drives the
return distribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ForecastInputs:
    starting_balance_cad: float
    annual_contribution_cad: float
    horizon_years: int
    equity_weight: float = 0.7
    bond_weight: float = 0.3
    target_cad: float | None = None
    n_simulations: int = 5000
    seed: int = 42

    equity_mean: float = 0.07
    equity_vol: float = 0.16
    bond_mean: float = 0.03
    bond_vol: float = 0.05
    inflation: float = 0.02

    def __post_init__(self) -> None:
        if abs((self.equity_weight + self.bond_weight) - 1.0) > 1e-6:
            raise ValueError("equity_weight + bond_weight must equal 1.0")
        if self.horizon_years <= 0:
            raise ValueError("horizon_years must be positive")


@dataclass
class ForecastResults:
    percentiles: dict[str, list[float]] = field(default_factory=dict)
    median_terminal: float = 0.0
    p10_terminal: float = 0.0
    p90_terminal: float = 0.0
    prob_hit_target: float | None = None
    real_median_terminal: float = 0.0


def run_forecast(inputs: ForecastInputs) -> ForecastResults:
    rng = np.random.default_rng(inputs.seed)

    portfolio_mean = (
        inputs.equity_weight * inputs.equity_mean
        + inputs.bond_weight * inputs.bond_mean
    )
    portfolio_vol = np.sqrt(
        (inputs.equity_weight * inputs.equity_vol) ** 2
        + (inputs.bond_weight * inputs.bond_vol) ** 2
    )

    n = inputs.n_simulations
    horizon = inputs.horizon_years

    returns = rng.normal(portfolio_mean, portfolio_vol, size=(n, horizon))
    balances = np.full(n, inputs.starting_balance_cad, dtype=np.float64)

    paths = np.zeros((n, horizon + 1))
    paths[:, 0] = balances

    for year in range(horizon):
        balances = balances * (1.0 + returns[:, year]) + inputs.annual_contribution_cad
        paths[:, year + 1] = balances

    pcts = {
        "p10": np.percentile(paths, 10, axis=0).tolist(),
        "p25": np.percentile(paths, 25, axis=0).tolist(),
        "p50": np.percentile(paths, 50, axis=0).tolist(),
        "p75": np.percentile(paths, 75, axis=0).tolist(),
        "p90": np.percentile(paths, 90, axis=0).tolist(),
    }

    terminal = paths[:, -1]
    real_deflator = (1.0 + inputs.inflation) ** horizon
    real_median = float(np.median(terminal) / real_deflator)

    prob_hit: float | None = None
    if inputs.target_cad is not None:
        prob_hit = float(np.mean(terminal >= inputs.target_cad))

    return ForecastResults(
        percentiles=pcts,
        median_terminal=float(np.median(terminal)),
        p10_terminal=float(np.percentile(terminal, 10)),
        p90_terminal=float(np.percentile(terminal, 90)),
        prob_hit_target=prob_hit,
        real_median_terminal=real_median,
    )
