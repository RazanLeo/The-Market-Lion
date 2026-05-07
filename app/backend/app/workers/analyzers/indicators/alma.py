"""Arnaud Legoux MA. Gaussian-weighted with offset (0.85) and sigma (6)."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "alma"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 9; offset = 0.85; sigma = 6
    if len(df) < n + 5: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    m = (n - 1) * offset; s = n / sigma
    weights = np.array([math.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(n)])
    weights /= weights.sum()
    alma = df["c"].rolling(n).apply(lambda x: float(np.dot(x, weights)), raw=True)
    v = float(alma.iloc[-1]); vp = float(alma.iloc[-5])
    slope = (v - vp) / vp * 100 if vp else 0
    last = float(df["c"].iloc[-1])
    payload = {"alma": round(v, 5), "slope_pct": round(slope, 3)}
    if last > v and slope > 0: return AnalyzerResult(CODE, "buy", min(75.0, 45 + slope * 6), WEIGHT_DEFAULT, payload)
    if last < v and slope < 0: return AnalyzerResult(CODE, "sell", min(75.0, 45 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class AlmaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
