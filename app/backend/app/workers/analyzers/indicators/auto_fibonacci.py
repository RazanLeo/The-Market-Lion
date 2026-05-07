"""Auto Fibonacci — auto-detected retracement levels from last directional leg.

Detects the most recent dominant leg (highest-high vs lowest-low within last 60 bars)
and projects 0.236 / 0.382 / 0.5 / 0.618 / 0.786 retracement levels. Returns a buy
signal if price is testing the 0.618 (golden ratio) from below and rebounding.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "auto_fibonacci"
WEIGHT_DEFAULT = 1.0
LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-60:]
    hi_i = int(win["h"].argmax()); lo_i = int(win["l"].argmin())
    hi = float(win["h"].iloc[hi_i]); lo = float(win["l"].iloc[lo_i])
    if hi <= lo:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_c = float(df["c"].iloc[-1])
    bullish_leg = lo_i < hi_i
    levels = {f"{lv:.3f}": (hi - (hi - lo) * lv if bullish_leg else lo + (hi - lo) * lv) for lv in LEVELS}
    pct_b = (last_c - lo) / (hi - lo)
    nearest_lvl = min(LEVELS, key=lambda lv: abs(pct_b - (1 - lv if bullish_leg else lv)))
    on_618 = abs(pct_b - (1 - 0.618 if bullish_leg else 0.618)) < 0.03
    payload = {"high": hi, "low": lo, "leg_dir": "up" if bullish_leg else "down",
               "levels": {k: round(v, 5) for k, v in levels.items()},
               "pct_in_leg": round(pct_b, 3), "nearest_level": nearest_lvl, "on_golden": on_618}
    if on_618 and bullish_leg and last_c > float(df["c"].iloc[-2]):
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if on_618 and not bullish_leg and last_c < float(df["c"].iloc[-2]):
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AutoFibonacciAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
