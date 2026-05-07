from app.services.backtest import run_simple_backtest


def _signal(df):
    if len(df) < 30: return {}
    if df["c"].iloc[-1] > df["c"].iloc[-30]: return {"side": "buy", "sl_distance": df["c"].iloc[-1]*0.005}
    return {"side": "sell", "sl_distance": df["c"].iloc[-1]*0.005}


def test_backtest_returns_result(ohlcv):
    r = run_simple_backtest(ohlcv, _signal)
    assert r.trades >= 0 and 0 <= r.win_rate <= 100
