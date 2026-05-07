"""Voting engine + Confluence scoring tests."""
from app.workers.engines.voting_engine import compute_confluence, AnalyzerResult


def test_unanimous_buy_high_confluence():
    fund = [AnalyzerResult("news", "buy", 80, 1.0)]
    bas = [AnalyzerResult(f"b{i}", "buy", 80, 1.0) for i in range(20)]
    sch = [AnalyzerResult(f"s{i}", "buy", 75, 1.0) for i in range(30)]
    ind = [AnalyzerResult(f"i{i}", "buy", 70, 1.0) for i in range(50)]
    flo = [AnalyzerResult(f"f{i}", "buy", 65, 1.0) for i in range(2)]
    out = compute_confluence(fund, bas, sch, ind, flo, threshold=80)
    assert out["direction"] == "buy"
    assert out["total_pct"] >= 60


def test_split_decision_yields_wait():
    fund = [AnalyzerResult("a", "buy", 50, 1.0), AnalyzerResult("b", "sell", 50, 1.0)]
    bas = [AnalyzerResult(f"b{i}", "neutral", 0, 1.0) for i in range(10)]
    sch = [AnalyzerResult(f"s{i}", "neutral", 0, 1.0) for i in range(10)]
    ind = [AnalyzerResult(f"i{i}", "neutral", 0, 1.0) for i in range(5)]
    flo = [AnalyzerResult("f", "neutral", 0, 1.0)]
    out = compute_confluence(fund, bas, sch, ind, flo, threshold=80)
    assert out["decision"] == "wait"


def test_majority_sell_signals_sell():
    fund = [AnalyzerResult("a", "sell", 80, 1.0)]
    bas = [AnalyzerResult(f"b{i}", "sell", 70, 1.0) for i in range(15)] + [AnalyzerResult(f"x{i}", "buy", 40, 1.0) for i in range(5)]
    sch = [AnalyzerResult(f"s{i}", "sell", 65, 1.0) for i in range(20)]
    ind = [AnalyzerResult(f"i{i}", "sell", 60, 1.0) for i in range(30)]
    flo = [AnalyzerResult("f", "sell", 60, 1.0)]
    out = compute_confluence(fund, bas, sch, ind, flo, threshold=70)
    assert out["direction"] == "sell"
