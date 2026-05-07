"""Wilder RSI(14)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "rsi"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    delta = df["c"].diff()
    up = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    dn = -delta.where(delta < 0, 0).ewm(alpha=1/14, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    last = float(rsi.iloc[-1])
    payload = {"rsi": round(last, 1)}
    if last < 30: return AnalyzerResult(CODE, "buy", min(80.0, 50 + (30 - last) * 1.5), WEIGHT_DEFAULT, payload)
    if last > 70: return AnalyzerResult(CODE, "sell", min(80.0, 50 + (last - 70) * 1.5), WEIGHT_DEFAULT, payload)
    if last > 55: return AnalyzerResult(CODE, "buy", 35, WEIGHT_DEFAULT, payload)
    if last < 45: return AnalyzerResult(CODE, "sell", 35, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class RsiIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
