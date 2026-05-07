"""Woodie Pivots. P = (H+L+2×C)/4 — weights close double; R1=2P-L; S1=2P-H."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "pivot_points_woodie"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 2: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    H = float(df["h"].iloc[-2]); L = float(df["l"].iloc[-2]); C = float(df["c"].iloc[-2])
    P = (H + L + 2 * C) / 4
    R1 = 2 * P - L; S1 = 2 * P - H
    R2 = P + (H - L); S2 = P - (H - L)
    last = float(df["c"].iloc[-1])
    payload = {"P": round(P, 5), "R1": round(R1, 5), "R2": round(R2, 5),
               "S1": round(S1, 5), "S2": round(S2, 5)}
    if last > R1 and last < R2: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if last < S1 and last > S2: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    if last >= R2: return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if last <= S2: return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class PivotPointsWoodieIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
