"""Rate of Change ROC = 100×(c - c[n])/c[n]. (n=12)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "roc"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 14: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    r = (c.iloc[-1] - c.iloc[-13]) / c.iloc[-13] * 100
    payload = {"roc": round(float(r), 2)}
    if r > 1: return AnalyzerResult(CODE, "buy", min(70.0, 40 + abs(float(r)) * 5), WEIGHT_DEFAULT, payload)
    if r < -1: return AnalyzerResult(CODE, "sell", min(70.0, 40 + abs(float(r)) * 5), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class RocIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
