"""Weighted Moving Average (period 20). Linear weights 1..n."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "wma"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    n = 20; w = np.arange(1, n + 1)
    wma = df["c"].rolling(n).apply(lambda x: float(np.dot(x, w) / w.sum()), raw=True)
    last = float(df["c"].iloc[-1]); v = float(wma.iloc[-1]); vp = float(wma.iloc[-5])
    slope = (v - vp) / vp * 100 if vp else 0
    payload = {"wma20": round(v, 5), "slope_pct": round(slope, 3)}
    if last > v and slope > 0: return AnalyzerResult(CODE, "buy", min(70.0, 40 + slope * 6), WEIGHT_DEFAULT, payload)
    if last < v and slope < 0: return AnalyzerResult(CODE, "sell", min(70.0, 40 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class WmaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
