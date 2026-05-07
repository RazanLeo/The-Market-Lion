"""Camarilla pivots. R/S levels at 1.1/12, 1.1/6, 1.1/4, 1.1/2 of range from close."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "pivot_points_camarilla"; WEIGHT_DEFAULT = 0.75
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 2: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    H = float(df["h"].iloc[-2]); L = float(df["l"].iloc[-2]); C = float(df["c"].iloc[-2])
    rng = H - L
    R1 = C + rng * 1.1 / 12; S1 = C - rng * 1.1 / 12
    R2 = C + rng * 1.1 / 6;  S2 = C - rng * 1.1 / 6
    R3 = C + rng * 1.1 / 4;  S3 = C - rng * 1.1 / 4
    R4 = C + rng * 1.1 / 2;  S4 = C - rng * 1.1 / 2
    last = float(df["c"].iloc[-1])
    payload = {"R1": round(R1, 5), "R2": round(R2, 5), "R3": round(R3, 5), "R4": round(R4, 5),
               "S1": round(S1, 5), "S2": round(S2, 5), "S3": round(S3, 5), "S4": round(S4, 5)}
    if last > R3: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)  # breakout buy
    if last < S3: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if last <= S3 and last > S4: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)  # reversal buy
    if last >= R3 and last < R4: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class PivotPointsCamarillaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
