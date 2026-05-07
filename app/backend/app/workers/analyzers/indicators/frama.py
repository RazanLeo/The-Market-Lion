"""Fractal Adaptive MA (Ehlers, 2005). Uses fractal dimension D to compute α = exp(-4.6×(D-1))."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "frama"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 16
    if len(df) < n * 2: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h = df["h"].astype(float); l = df["l"].astype(float); c = df["c"].astype(float)
    frama = pd.Series(index=df.index, dtype=float)
    frama.iloc[n - 1] = float(c.iloc[:n].mean())
    half = n // 2
    for i in range(n, len(df)):
        h1 = float(h.iloc[i - n:i - half].max()); l1 = float(l.iloc[i - n:i - half].min())
        h2 = float(h.iloc[i - half:i].max()); l2 = float(l.iloc[i - half:i].min())
        h3 = float(h.iloc[i - n:i].max()); l3 = float(l.iloc[i - n:i].min())
        n1 = (h1 - l1) / half if half else 0
        n2 = (h2 - l2) / half if half else 0
        n3 = (h3 - l3) / n if n else 0
        if n1 > 0 and n2 > 0 and n3 > 0:
            d = (math.log(n1 + n2) - math.log(n3)) / math.log(2)
        else:
            d = 1.5
        d = max(1.0, min(2.0, d))
        alpha = math.exp(-4.6 * (d - 1))
        alpha = max(0.01, min(1.0, alpha))
        frama.iloc[i] = alpha * float(c.iloc[i]) + (1 - alpha) * float(frama.iloc[i - 1])
    v = float(frama.iloc[-1]); vp = float(frama.iloc[-5])
    slope = (v - vp) / vp * 100 if vp else 0
    last = float(c.iloc[-1])
    payload = {"frama": round(v, 5), "slope_pct": round(slope, 3)}
    if last > v and slope > 0: return AnalyzerResult(CODE, "buy", min(70.0, 40 + slope * 6), WEIGHT_DEFAULT, payload)
    if last < v and slope < 0: return AnalyzerResult(CODE, "sell", min(70.0, 40 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class FramaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
