"""Lion Sigmoid Trailing Stop — adaptive ATR trail.

Distance from price = ATR × sigmoid(slope × k), where slope = (close - close.shift(20))
normalized by ATR. Strong trends → wider trail (lets winners run); flat → tighter trail.
"""
from __future__ import annotations
import math
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_sigmoid_trail_ind"
WEIGHT_DEFAULT = 0.6


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    last_c = float(c.iloc[-1])
    slope_20 = (last_c - float(c.iloc[-21])) / 20
    atr = float(_atr(df).iloc[-1] or 1e-9)
    slope_norm = slope_20 / atr
    k = 3.0
    sigmoid = 1.0 / (1.0 + math.exp(-k * slope_norm))
    multiplier = 1 + 3 * (sigmoid - 0.5) * 2  # range 1..4 for strong up, 1..-2 for down
    multiplier = max(1.0, min(4.0, abs(multiplier)))
    distance = atr * multiplier
    sl_long = last_c - distance; sl_short = last_c + distance
    trend_up = slope_20 > 0
    payload = {"atr": round(atr, 5), "slope_norm": round(slope_norm, 3),
               "sigmoid": round(sigmoid, 3), "multiplier": round(multiplier, 2),
               "trail_distance": round(distance, 5),
               "SL_long": round(sl_long, 5), "SL_short": round(sl_short, 5),
               "trend": "up" if trend_up else "down"}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionSigmoidTrailIndAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
