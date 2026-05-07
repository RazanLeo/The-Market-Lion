"""Fibonacci Analysis — multi-timeframe fib confluence.

Computes fib retracements over 3 lookback windows: 30, 60, 120 bars. Counts how many
fib levels (across all 3 timeframes) the current close is touching within tol=0.3×ATR.
2+ confluence = strong reaction zone.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_analysis"
WEIGHT_DEFAULT = 1.0
LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 130:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    last_c = float(df["c"].iloc[-1])
    confluence = 0
    hits_detail = []
    for window in (30, 60, 120):
        win = df.iloc[-window:]
        hi = float(win["h"].max()); lo = float(win["l"].min())
        if hi <= lo: continue
        bullish = int(win["l"].argmin()) < int(win["h"].argmax())
        for lv in LEVELS:
            level_p = hi - (hi - lo) * lv if bullish else lo + (hi - lo) * lv
            if abs(last_c - level_p) < atr * 0.3:
                confluence += 1
                hits_detail.append((window, lv, round(level_p, 5)))
    momentum = float(df["c"].iloc[-1]) - float(df["c"].iloc[-3])
    payload = {"fib_confluence_count": confluence, "hits": hits_detail[:8],
               "momentum_3b": round(momentum, 5)}
    if confluence >= 3 and momentum > 0:
        return AnalyzerResult(CODE, "buy", min(85, 50 + confluence * 8), WEIGHT_DEFAULT, payload)
    if confluence >= 3 and momentum < 0:
        return AnalyzerResult(CODE, "sell", min(85, 50 + confluence * 8), WEIGHT_DEFAULT, payload)
    if confluence >= 2:
        return AnalyzerResult(CODE, "neutral", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FibonacciAnalysisAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
