"""Market regime classifier.

Four regimes: calm, normal, elevated, crisis.
Features: trailing 30d realized vol, trailing 60d return, term spread proxy,
HY credit proxy. sklearn pipeline saved as a versioned joblib pickle.
The training script lives in scripts/train_regime.py (not included yet).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

REGIMES = ("calm", "normal", "elevated", "crisis")


@dataclass
class RegimeFeatures:
    realized_vol_30d: float
    return_60d: float
    term_spread: float
    credit_spread: float

    def to_array(self) -> np.ndarray:
        return np.array(
            [self.realized_vol_30d, self.return_60d, self.term_spread, self.credit_spread]
        )


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(random_state=42)),
        ]
    )


def walk_forward_validate(
    X: np.ndarray, y: np.ndarray, n_splits: int = 5
) -> list[float]:
    """Time-respecting walk-forward CV. Returns accuracy per fold."""
    n = len(y)
    if n_splits < 2 or n < n_splits + 1:
        raise ValueError("not enough samples for requested splits")

    fold_size = n // (n_splits + 1)
    accuracies: list[float] = []
    for fold in range(n_splits):
        train_end = fold_size * (fold + 1)
        test_end = train_end + fold_size
        if test_end > n:
            break
        pipe = build_pipeline()
        pipe.fit(X[:train_end], y[:train_end])
        score = pipe.score(X[train_end:test_end], y[train_end:test_end])
        accuracies.append(float(score))
    return accuracies


def predict_regime(model: Pipeline, features: RegimeFeatures) -> str:
    label_idx = int(model.predict(features.to_array().reshape(1, -1))[0])
    return REGIMES[label_idx]
