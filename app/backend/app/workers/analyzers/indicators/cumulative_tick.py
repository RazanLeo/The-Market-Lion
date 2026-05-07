"""Cumulative Tick — proxy of NYSE TICK using bar direction count.

Cumulative TICK adds +1 for each up-bar, -1 for each down-bar, 0 for doji. Reading > +500
historically signals overbought, < -500 oversold. Here we apply a rolling 100-bar
cumulative window to single-instrument data.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "cumulative_tick"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 120:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    diff = df["c"] - df["c"].shift(1)
    tick = np.sign(diff).fillna(0)
    cum_tick = tick.rolling(100).sum()
    last = float(cum_tick.iloc[-1])
    prev = float(cum_tick.iloc[-2])
    payload = {"cumulative_tick_100b": round(last, 1), "prev": round(prev, 1)}
    if last < -30 and prev <= last:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if last > 30 and prev >= last:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if last > 50:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    if last < -50:
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CumulativeTickAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
