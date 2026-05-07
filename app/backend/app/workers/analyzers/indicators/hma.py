"""Hull Moving Average: HMA = WMA(2×WMA(price, n/2) - WMA(price, n), sqrt(n))."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "hma"; WEIGHT_DEFAULT = 1.0
def _wma(s, n):
    w = np.arange(1, n + 1)
    return s.rolling(n).apply(lambda x: float(np.dot(x, w) / w.sum()), raw=True)
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 16
    if len(df) < n + int(math.sqrt(n)) + 5: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    half = _wma(df["c"], n // 2); full = _wma(df["c"], n)
    raw = 2 * half - full
    hma = _wma(raw, int(math.sqrt(n)))
    last = float(df["c"].iloc[-1]); v = float(hma.iloc[-1]); vp = float(hma.iloc[-5])
    slope = (v - vp) / vp * 100 if vp else 0
    payload = {"hma": round(v, 5), "slope_pct": round(slope, 3)}
    if last > v and slope > 0: return AnalyzerResult(CODE, "buy", min(75.0, 45 + slope * 6), WEIGHT_DEFAULT, payload)
    if last < v and slope < 0: return AnalyzerResult(CODE, "sell", min(75.0, 45 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class HmaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
