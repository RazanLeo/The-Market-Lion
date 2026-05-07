"""Full registry smoke — every school + indicator + tool runs without error and returns valid AnalyzerResult."""
import os
os.environ.setdefault("JWT_SECRET", "x" * 64)
os.environ.setdefault("ENCRYPTION_KEY", "y" * 32)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
import numpy as np
import pandas as pd
import pytest
from app.workers.analyzers._registry import SCHOOLS, INDICATORS, TOOLS


@pytest.fixture(scope="module")
def big_df():
    rng = np.random.default_rng(11)
    n = 300; rets = rng.normal(0.0001, 0.005, n); prices = 2300 * (1 + rets).cumprod()
    df = pd.DataFrame({"o": prices, "h": prices*1.002, "l": prices*0.998, "c": prices, "v": rng.integers(100, 5000, n).astype(float)})
    df.index = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    return df


def test_schools_count_at_least_89():
    assert len(SCHOOLS) >= 89, f"only {len(SCHOOLS)} schools registered"


def test_indicators_count_at_least_120():
    assert len(INDICATORS) >= 120, f"only {len(INDICATORS)} indicators registered"


def test_tools_count_exactly_20():
    assert len(TOOLS) == 20, f"got {len(TOOLS)} tools"


def test_all_schools_run(big_df):
    for code, fn in SCHOOLS.items():
        r = fn(big_df)
        assert r.result in ("buy", "sell", "neutral"), f"{code} bad result"
        assert 0 <= r.confidence <= 100


def test_all_indicators_run(big_df):
    for code, fn in INDICATORS.items():
        r = fn(big_df)
        assert r.result in ("buy", "sell", "neutral"), f"{code} bad result"


def test_all_tools_run(big_df):
    for code, fn in TOOLS.items():
        r = fn(big_df)
        assert r.result in ("buy", "sell", "neutral")
        assert "drawings" in r.payload
