"""Exponential Moving Average (period 20). EMA[i] = α×price + (1-α)×EMA[i-1], α=2/(n+1)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "ema"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ema = df["c"].ewm(span=20, adjust=False).mean()
    last = float(df["c"].iloc[-1]); e = float(ema.iloc[-1]); e_prev = float(ema.iloc[-5])
    slope = (e - e_prev) / e_prev * 100 if e_prev else 0
    payload = {"ema20": round(e, 5), "slope_5bars_pct": round(slope, 3)}
    if last > e and slope > 0: return AnalyzerResult(CODE, "buy", min(75.0, 45 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    if last < e and slope < 0: return AnalyzerResult(CODE, "sell", min(75.0, 45 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class EmaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
