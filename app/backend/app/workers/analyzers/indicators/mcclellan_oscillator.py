"""McClellan Oscillator — EMA(19) − EMA(39) of advance-decline differential.

Standard McClellan uses NYSE A-D net. Single-instrument proxy: signed bar direction
(+1 up, -1 down). Then EMA(19) and EMA(39) are computed and differenced. Cross above
zero = buy momentum, below zero = sell momentum.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "mcclellan_oscillator"
WEIGHT_DEFAULT = 0.8


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    diff = np.sign(df["c"] - df["c"].shift(1)).fillna(0).astype(float)
    ema19 = diff.ewm(span=19, adjust=False).mean()
    ema39 = diff.ewm(span=39, adjust=False).mean()
    osc = (ema19 - ema39) * 100
    last = float(osc.iloc[-1])
    prev = float(osc.iloc[-2])
    payload = {"mcclellan": round(last, 2), "prev": round(prev, 2),
               "ema19": round(float(ema19.iloc[-1]) * 100, 3),
               "ema39": round(float(ema39.iloc[-1]) * 100, 3)}
    if prev <= 0 < last:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if prev >= 0 > last:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if last > 30:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)  # overbought
    if last < -30:
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)  # oversold
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class McclellanOscillatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
