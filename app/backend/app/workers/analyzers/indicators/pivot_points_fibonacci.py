"""Fibonacci Pivots. P=(H+L+C)/3; R1=P+0.382×(H-L); R2=P+0.618×(H-L); R3=P+1×(H-L); mirror for S."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "pivot_points_fibonacci"; WEIGHT_DEFAULT = 0.75
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 2: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    H = float(df["h"].iloc[-2]); L = float(df["l"].iloc[-2]); C = float(df["c"].iloc[-2])
    P = (H + L + C) / 3; rng = H - L
    R1 = P + 0.382 * rng; R2 = P + 0.618 * rng; R3 = P + rng
    S1 = P - 0.382 * rng; S2 = P - 0.618 * rng; S3 = P - rng
    last = float(df["c"].iloc[-1])
    payload = {"P": round(P, 5), "R1": round(R1, 5), "R2": round(R2, 5), "R3": round(R3, 5),
               "S1": round(S1, 5), "S2": round(S2, 5), "S3": round(S3, 5)}
    if last > R2: return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if last < S2: return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if last > R1: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    if last < S1: return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class PivotPointsFibonacciIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
