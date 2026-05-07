"""Pytest fixtures — including OHLCV synthesizer and mocked Capital.com adapter."""
import os
os.environ.setdefault("JWT_SECRET", "x" * 64)
os.environ.setdefault("ENCRYPTION_KEY", "y" * 32)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import numpy as np
import pandas as pd
import pytest


def _gen_ohlcv(n: int = 300, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 2300.0
    rets = rng.normal(0, 0.005, n)
    prices = base * (1 + rets).cumprod()
    rows = []
    for i, p in enumerate(prices):
        o = p; c = p * (1 + rng.normal(0, 0.002))
        h = max(o, c) * (1 + abs(rng.normal(0, 0.002)))
        l = min(o, c) * (1 - abs(rng.normal(0, 0.002)))
        v = float(rng.integers(100, 5000))
        rows.append({"o": o, "h": h, "l": l, "c": c, "v": v})
    df = pd.DataFrame(rows)
    df.index = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    return df


@pytest.fixture
def ohlcv() -> pd.DataFrame: return _gen_ohlcv()


@pytest.fixture
def small_ohlcv() -> pd.DataFrame: return _gen_ohlcv(50)
