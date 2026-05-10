"""Train the regime classifier.

Pulls daily SPY + TLT + ^VIX history from Yahoo, builds features, labels
each day's regime via a rule-based heuristic, runs walk-forward
validation, and saves the fitted pipeline.

Run:  python -m scripts.train_regime --years 12

The labels are heuristic, not ground truth — once we have richer data,
revisit. The goal here is a reproducible baseline.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.ml.regime_classifier import REGIMES, build_pipeline, walk_forward_validate

MODEL_PATH = Path(os.environ.get("REGIME_MODEL_PATH", "joblib_models/regime_v1.pkl"))


def _label(vol: float, ret60: float) -> int:
    """Heuristic 4-class label.

    calm:     low vol, positive return
    normal:   moderate vol, any return
    elevated: high vol or sustained drawdown
    crisis:   very high vol and large drawdown
    """
    if vol > 0.40 and ret60 < -0.10:
        return REGIMES.index("crisis")
    if vol > 0.25 or ret60 < -0.08:
        return REGIMES.index("elevated")
    if vol < 0.12 and ret60 > 0.0:
        return REGIMES.index("calm")
    return REGIMES.index("normal")


def _build_features(years: int) -> tuple[np.ndarray, np.ndarray]:
    import yfinance as yf

    spy = yf.download("SPY", period=f"{years}y", interval="1d", auto_adjust=True, progress=False)
    tlt = yf.download("TLT", period=f"{years}y", interval="1d", auto_adjust=True, progress=False)
    vix = yf.download("^VIX", period=f"{years}y", interval="1d", auto_adjust=True, progress=False)

    df = pd.DataFrame({
        "spy_ret": spy["Close"].pct_change(),
        "tlt_ret": tlt["Close"].pct_change(),
        "vix": vix["Close"],
    }).dropna()

    df["realized_vol_30d"] = df["spy_ret"].rolling(30).std() * np.sqrt(252)
    df["return_60d"] = (1 + df["spy_ret"]).rolling(60).apply(np.prod, raw=True) - 1
    df["term_spread"] = df["tlt_ret"].rolling(30).mean() * 252  # crude proxy
    df["credit_spread"] = df["vix"] / df["vix"].rolling(252).mean()
    df = df.dropna()

    X = df[["realized_vol_30d", "return_60d", "term_spread", "credit_spread"]].to_numpy()
    y = np.array([_label(v, r) for v, r in zip(df["realized_vol_30d"], df["return_60d"])])
    return X, y


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=12)
    parser.add_argument("--save", action="store_true", default=True)
    args = parser.parse_args()

    X, y = _build_features(args.years)
    print(f"features: {X.shape}, label distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    accs = walk_forward_validate(X, y, n_splits=5)
    print(f"walk-forward accuracies: {[round(a, 3) for a in accs]}, mean={np.mean(accs):.3f}")

    if args.save:
        pipeline = build_pipeline()
        pipeline.fit(X, y)
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"version": "v1", "pipeline": pipeline, "features": [
            "realized_vol_30d", "return_60d", "term_spread", "credit_spread",
        ]}, MODEL_PATH)
        print(f"saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
