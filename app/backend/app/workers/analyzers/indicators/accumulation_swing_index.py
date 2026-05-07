"""Wilder Accumulation Swing Index (ASI). Cumulative SI."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "accumulation_swing_index"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o, h, l, c = df["o"].astype(float), df["h"].astype(float), df["l"].astype(float), df["c"].astype(float)
    L = 3.0  # limit move (proxy)
    si = pd.Series(index=df.index, dtype=float); si.iloc[0] = 0
    for i in range(1, len(df)):
        K = max(abs(h.iloc[i] - c.iloc[i-1]), abs(l.iloc[i] - c.iloc[i-1]))
        T1 = abs(h.iloc[i] - c.iloc[i-1]); T2 = abs(l.iloc[i] - c.iloc[i-1])
        T3 = abs(c.iloc[i-1] - o.iloc[i-1])
        if T1 > T2 and T1 > T3: R = T1 - 0.5 * T2 + 0.25 * T3
        elif T2 > T1 and T2 > T3: R = T2 - 0.5 * T1 + 0.25 * T3
        else: R = T3 + 0.25 * (T1 - T2 if T1 > T2 else T2 - T1)
        if R == 0 or L == 0: si.iloc[i] = 0
        else:
            si_val = 50 * ((c.iloc[i] - c.iloc[i-1]) + 0.5 * (c.iloc[i] - o.iloc[i]) + 0.25 * (c.iloc[i-1] - o.iloc[i-1])) / R * (K / L)
            si.iloc[i] = float(si_val)
    asi = si.cumsum()
    last = float(asi.iloc[-1]); prev = float(asi.iloc[-10])
    rising = last > prev
    payload = {"asi": round(last, 2), "rising": rising}
    if rising: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
class AccumulationSwingIndexIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
