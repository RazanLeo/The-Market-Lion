"""DeMark Pivot. X = H+L+2C if C<O; H+L+2C if C>O (variation); else H+L+C. Pivot=X/4."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "pivot_points_demark"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 2: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    O = float(df["o"].iloc[-2]); H = float(df["h"].iloc[-2])
    L = float(df["l"].iloc[-2]); C = float(df["c"].iloc[-2])
    if C < O: X = H + 2 * L + C
    elif C > O: X = 2 * H + L + C
    else: X = H + L + 2 * C
    P = X / 4
    R1 = X / 2 - L; S1 = X / 2 - H
    last = float(df["c"].iloc[-1])
    payload = {"P": round(P, 5), "R1": round(R1, 5), "S1": round(S1, 5)}
    if last > R1: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if last < S1: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class PivotPointsDemarkIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
