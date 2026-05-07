"""Momentum = close - close[N back]. (n=14)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "momentum"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 16: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last = float(df["c"].iloc[-1]); prev = float(df["c"].iloc[-15])
    m = last - prev
    pct = m / prev * 100 if prev else 0
    payload = {"momentum": round(m, 5), "pct": round(pct, 2)}
    if pct > 1: return AnalyzerResult(CODE, "buy", min(70.0, 40 + abs(pct) * 4), WEIGHT_DEFAULT, payload)
    if pct < -1: return AnalyzerResult(CODE, "sell", min(70.0, 40 + abs(pct) * 4), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class MomentumIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
