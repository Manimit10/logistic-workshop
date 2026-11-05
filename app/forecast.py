"""Demand forecasting: gradient-boosted *quantile* models, one per horizon.

The same recipe is used in notebooks/forecasting_colab.ipynb. Models are trained
on synthetic series (never on the live game data), then saved to artifacts/.
Features are scale-free (lags divided by the recent level) so one model serves
SKUs of very different size.
"""
from __future__ import annotations

import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

QUANTILES = (0.5, 0.8, 0.95)
HORIZONS = (1, 2, 3, 4)       # h=1 -> next round, h=4 -> three rounds after that
N_LAGS = 6
ARTIFACT = Path(__file__).resolve().parent.parent / "artifacts" / "forecast_models.joblib"


def features(y: np.ndarray, t: int) -> tuple[np.ndarray, float]:
    """Features from observations y[:t]; returns (vector, level)."""
    w = np.asarray(y[t - N_LAGS: t], dtype=float)
    level = max(float(w.mean()), 1.0)
    lags = w / level
    slope = (w[-3:].mean() - w[:3].mean()) / level
    ratio_last = w[-1] / level
    return np.concatenate([lags, [slope, ratio_last]]), level


def _synthetic_series(rng: np.random.Generator, n: int = 36) -> np.ndarray:
    """Random mix of stable / trending / seasonal / spiky demand."""
    t = np.arange(n)
    base = rng.uniform(15, 200)
    kind = rng.choice(["flat", "trend", "season", "spike"])
    mean = np.full(n, base)
    if kind == "trend":
        mean = base * (1 + rng.uniform(-0.03, 0.09)) ** t
    elif kind == "season":
        mean = base * (1 + rng.uniform(0.2, 0.6) * np.sin(2 * np.pi * t / rng.uniform(8, 16) + rng.uniform(0, 6.3)))
    elif kind == "spike":
        for _ in range(rng.integers(1, 4)):
            s = rng.integers(8, n - 5)
            mean[s: s + rng.integers(2, 5)] *= rng.uniform(2, 7)
    sigma = rng.uniform(0.08, 0.3)
    return np.maximum(0, np.rint(mean * rng.lognormal(0, sigma, n)))


def make_training_data(n_series: int = 500, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    data = {h: ([], []) for h in HORIZONS}
    for _ in range(n_series):
        y = _synthetic_series(rng)
        for t in range(N_LAGS, len(y) - max(HORIZONS) + 1):
            x, level = features(y, t)
            for h in HORIZONS:
                data[h][0].append(x)
                data[h][1].append(y[t + h - 1] / level)
    return {h: (np.array(X), np.array(Y)) for h, (X, Y) in data.items()}


def train(n_series: int = 500, seed: int = 0) -> dict:
    data = make_training_data(n_series, seed)
    models = {}
    for h, (X, Y) in data.items():
        for q in QUANTILES:
            m = GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=80, max_depth=3,
                                          learning_rate=0.1, subsample=0.8, random_state=seed)
            models[(h, q)] = m.fit(X, Y)
    return models


_MODELS: dict | None = None


def get_models() -> dict:
    global _MODELS
    if _MODELS is None:
        try:
            _MODELS = joblib.load(ARTIFACT)
        except Exception:                      # missing file or sklearn version mismatch
            _MODELS = train()
            try:
                ARTIFACT.parent.mkdir(exist_ok=True)
                joblib.dump(_MODELS, ARTIFACT, compress=3)
            except OSError:
                pass
    return _MODELS


def forecast(history: list[float]) -> dict[int, dict[str, int]]:
    """{h: {'p50':..,'p80':..,'p95':..}} for demand h rounds ahead (h=1 is next round)."""
    y = np.asarray(history, dtype=float)
    x, level = features(y, len(y))
    models = get_models()
    out = {}
    for h in HORIZONS:
        vals = sorted(float(models[(h, q)].predict(x.reshape(1, -1))[0]) * level for q in QUANTILES)
        out[h] = {"p50": max(0, round(vals[0])), "p80": max(0, round(vals[1])), "p95": max(0, round(vals[2]))}
    return out


def quantile_at(fc_h: dict[str, int], q: float) -> float:
    """Interpolate a demand quantile from p50/p80/p95 (flat beyond the ends)."""
    pts = [(0.5, fc_h["p50"]), (0.8, fc_h["p80"]), (0.95, fc_h["p95"])]
    if q <= 0.5:
        return pts[0][1] * max(q, 0.0) / 0.5 if q < 0.5 else pts[0][1]
    for (q0, v0), (q1, v1) in zip(pts, pts[1:]):
        if q <= q1:
            return v0 + (v1 - v0) * (q - q0) / (q1 - q0)
    return pts[-1][1]


if __name__ == "__main__":   # python -m app.forecast  -> (re)build the artifact
    ARTIFACT.parent.mkdir(exist_ok=True)
    joblib.dump(train(), ARTIFACT, compress=3)
    print("saved", ARTIFACT, os.path.getsize(ARTIFACT) // 1024, "KB")
