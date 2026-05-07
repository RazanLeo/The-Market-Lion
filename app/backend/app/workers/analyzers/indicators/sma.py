"""Simple Moving Average (period 20)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "sma"
WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sma = df["c"].rolling(20).mean()
    last = float(df["c"].iloc[-1]); s = float(sma.iloc[-1]); s_prev = float(sma.iloc[-5])
    slope = (s - s_prev) / s_prev * 100 if s_prev else 0
    payload = {"sma20": round(s, 5), "slope_5bars_pct": round(slope, 3)}
    if last > s and slope > 0: return AnalyzerResult(CODE, "buy", min(70.0, 40 + abs(slope) * 5), WEIGHT_DEFAULT, payload)
    if last < s and slope < 0: return AnalyzerResult(CODE, "sell", min(70.0, 40 + abs(slope) * 5), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class SmaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
