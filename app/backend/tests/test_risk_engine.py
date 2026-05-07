"""Risk engine — position sizing + leverage + R-multiples."""
import asyncio
import pandas as pd
import pytest
from app.workers.engines.risk_engine import _select_leverage, _ohlcv_to_df


def test_leverage_buckets():
    assert _select_leverage(500) == 30
    assert _select_leverage(5000) == 100
    assert _select_leverage(20_000) == 200
    assert _select_leverage(100_000) == 500


def test_ohlcv_parser_handles_empty():
    df = _ohlcv_to_df([])
    assert df.empty


def test_ohlcv_parser_handles_normal():
    rows = [{
        "snapshotTimeUTC": "2026-01-01T00:00:00Z",
        "openPrice": {"bid": 2300}, "highPrice": {"bid": 2305},
        "lowPrice": {"bid": 2298}, "closePrice": {"bid": 2302},
        "lastTradedVolume": 1500,
    }]
    df = _ohlcv_to_df(rows)
    assert len(df) == 1
    assert df["c"].iloc[0] == 2302
