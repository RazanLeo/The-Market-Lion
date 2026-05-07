"""Detrended Price Oscillator = price - SMA20 shifted by (n/2 + 1)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "detrended_price_osc"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 20
    if len(df) < n + 15: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sma = df["c"].rolling(n).mean()
    dpo = df["c"] - sma.shift(n // 2 + 1)
    last = float(dpo.iloc[-1])
    payload = {"dpo": round(last, 5)}
    if last > 0: return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    if last < 0: return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class DetrendedPriceOscIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
