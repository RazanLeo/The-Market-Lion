"""Fibonacci Retracement — auto-applied to last directional leg.

Identifies last leg from highest-high to lowest-low (or vice versa) within last 80
bars, then computes 0.236 / 0.382 / 0.5 / 0.618 / 0.786 levels. Buy at 0.618 in an
uptrend, sell at 0.618 in downtrend (with momentum confirmation).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_retracement"
WEIGHT_DEFAULT = 1.0
LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-80:]
    hi_i = int(win["h"].argmax()); lo_i = int(win["l"].argmin())
    hi = float(win["h"].iloc[hi_i]); lo = float(win["l"].iloc[lo_i])
    if hi <= lo:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    bullish = lo_i < hi_i
    last_c = float(df["c"].iloc[-1])
    levels_dict = {}
    for lv in LEVELS:
        levels_dict[f"{lv:.3f}"] = round(hi - (hi - lo) * lv if bullish else lo + (hi - lo) * lv, 5)
    pct_b = (last_c - lo) / (hi - lo)
    target_618 = (1 - 0.618) if bullish else 0.618
    on_618 = abs(pct_b - target_618) < 0.025
    target_50 = 0.5
    on_50 = abs(pct_b - target_50) < 0.02
    payload = {"high": hi, "low": lo, "leg": "up" if bullish else "down",
               "levels": levels_dict, "pct_in_leg": round(pct_b, 3),
               "on_0.618": on_618, "on_0.5": on_50}
    momentum = float(df["c"].iloc[-1]) - float(df["c"].iloc[-3])
    if bullish and on_618 and momentum > 0:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if (not bullish) and on_618 and momentum < 0:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if bullish and on_50:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if (not bullish) and on_50:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FibonacciRetracementAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
