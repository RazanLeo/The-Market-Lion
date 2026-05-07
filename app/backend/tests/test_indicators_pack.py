"""Smoke tests for indicator analyzers."""
import pandas as pd
from app.workers.analyzers import indicators_pack as p1, indicators_pack_2 as p2


def test_rsi(ohlcv):
    r = p1.rsi_analyzer(ohlcv)
    assert r.code == "rsi"
    assert r.result in ("buy", "sell", "neutral")
    assert 0 <= r.confidence <= 100


def test_ema_stack(ohlcv): assert p1.ema_stack_analyzer(ohlcv).code == "ema_stack"
def test_macd(ohlcv): assert p1.macd_analyzer(ohlcv).code == "macd"
def test_vwap(ohlcv): assert p1.vwap_analyzer(ohlcv).code == "vwap"
def test_bollinger(ohlcv): assert p1.bollinger_analyzer(ohlcv).code == "bollinger"
def test_atr_vol(ohlcv): assert p1.atr_volatility_analyzer(ohlcv).code == "atr_vol"
def test_adx(ohlcv): assert p1.adx_analyzer(ohlcv).code == "adx"


def test_pack2_smoke(ohlcv):
    """Run all p2 indicator analyzers; ensure they don't crash."""
    fns = [
        p2.stochastic, p2.stochastic_rsi, p2.williams_r, p2.roc, p2.awesome_oscillator,
        p2.momentum_indicator, p2.mfi, p2.ultimate_oscillator, p2.aroon, p2.vortex,
        p2.coppock, p2.chande_momentum, p2.kst, p2.tsi, p2.schaff_trend_cycle,
        p2.fisher_transform, p2.keltner, p2.donchian, p2.std_dev, p2.historical_vol,
        p2.chaikin_volatility, p2.mass_index, p2.choppiness, p2.bbw, p2.obv,
        p2.ad_line, p2.cmf, p2.klinger, p2.force_index, p2.ease_of_movement,
        p2.volume_oscillator, p2.anchored_vwap, p2.cumulative_delta, p2.supertrend,
        p2.linreg, p2.zigzag, p2.parabolic_sar, p2.ichimoku, p2.demarker,
        p2.pivot_points_classic, p2.auto_sr, p2.auto_fib, p2.auto_trend_lines,
    ]
    for fn in fns:
        r = fn(ohlcv)
        assert r.result in ("buy", "sell", "neutral"), f"{fn.__name__} returned bad result"
