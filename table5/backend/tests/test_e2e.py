# ═══════════════════════════════════════════════════════════════════════════
# 🦁 اختبار شامل لكل المؤشرات الـ 71 + محرك التصويت + API
# ═══════════════════════════════════════════════════════════════════════════
import asyncio
import os
from datetime import datetime, timezone

import pandas as pd
import pytest

os.environ["MARKET_DATA_SOURCE"] = "mock"

from app.indicators.registry import (
    get_all_71_indicators, verify_total_weight, count_by_tier,
)
from app.services.market_data import fetch_ohlcv_per_tf
from app.voting.engine import Table5VotingEngine


def test_count_71():
    inds = get_all_71_indicators()
    assert len(inds) == 71


def test_ids_sequential():
    inds = get_all_71_indicators()
    for i, ind in enumerate(inds, start=1):
        assert ind.id == i


def test_tier_distribution():
    counts = count_by_tier()
    assert counts == {"S": 13, "A": 11, "B": 34, "C": 13}


def test_total_weight_exactly_10pct():
    assert verify_total_weight()
    total = sum(i.weight for i in get_all_71_indicators())
    assert abs(total - 0.10) < 1e-9


def test_each_indicator_returns_valid_signal():
    """كل المؤشرات الـ71 تُرجع 'شراء' أو 'بيع' أو 'محايد' بدون استثناء"""
    ohlcv = asyncio.run(fetch_ohlcv_per_tf("XAU/USD"))
    df = ohlcv["1H"]
    failed = []
    for ind in get_all_71_indicators():
        try:
            sig = ind.compute_signal(df)
            assert sig in ("شراء", "بيع", "محايد"), f"#{ind.id}: '{sig}'"
        except Exception as e:
            failed.append(f"#{ind.id} {ind.name}: {e}")
    assert not failed, "مؤشرات فشلت: " + " | ".join(failed)


def test_voting_engine_xauusd():
    eng = Table5VotingEngine()
    ohlcv = asyncio.run(fetch_ohlcv_per_tf("XAU/USD"))
    d = eng.evaluate("XAU/USD", datetime.now(timezone.utc).isoformat(), ohlcv)
    assert d.decision in ("شراء", "بيع", "محايد")
    assert -1.0 <= d.net_score <= 1.0
    assert 0.0 <= d.confidence <= 1.0
    assert len(d.indicators) == 71


def test_voting_engine_xtiusd():
    eng = Table5VotingEngine()
    ohlcv = asyncio.run(fetch_ohlcv_per_tf("XTI/USD"))
    d = eng.evaluate("XTI/USD", datetime.now(timezone.utc).isoformat(), ohlcv)
    assert d.decision in ("شراء", "بيع", "محايد")
    assert len(d.indicators) == 71


def test_evaluate_all_timeframes_returns_6():
    ohlcv = asyncio.run(fetch_ohlcv_per_tf("XAU/USD"))
    ind = get_all_71_indicators()[0]
    res = ind.evaluate_all_timeframes(ohlcv)
    assert set(res.signals.keys()) == {"1M", "5M", "15M", "30M", "1H", "4H"}
    for tf, sig in res.signals.items():
        assert sig in ("شراء", "بيع", "محايد")


def test_api_decision_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/api/v1/table-5/decision", params={"symbol": "XAU/USD"})
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] in ("شراء", "بيع", "محايد")
    assert d["indicators"] and len(d["indicators"]) == 71


def test_api_meta_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/api/v1/table-5/meta")
    assert r.status_code == 200
    m = r.json()
    assert m["module_weight_pct"] == 10.0
    assert m["indicators_count"] == 71
    assert m["timeframes"] == ["1M", "5M", "15M", "30M", "1H", "4H"]
    assert m["tier_distribution"] == {"S": 13, "A": 11, "B": 34, "C": 13}


if __name__ == "__main__":
    test_count_71()
    test_ids_sequential()
    test_tier_distribution()
    test_total_weight_exactly_10pct()
    test_each_indicator_returns_valid_signal()
    test_voting_engine_xauusd()
    test_voting_engine_xtiusd()
    test_evaluate_all_timeframes_returns_6()
    test_api_decision_endpoint()
    test_api_meta_endpoint()
    print("✅ كل الاختبارات الـ 10 نجحت")
