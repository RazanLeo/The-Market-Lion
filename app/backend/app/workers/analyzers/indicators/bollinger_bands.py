"""Bollinger Bands (20, 2): mid = SMA20; upper = mid + 2σ; lower = mid - 2σ."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "bollinger_bands"; WEIGHT_DEFAULT = 0.95
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sma = df["c"].rolling(20).mean(); sd = df["c"].rolling(20).std()
    upper = sma + 2 * sd; lower = sma - 2 * sd
    last = float(df["c"].iloc[-1]); u = float(upper.iloc[-1]); lo = float(lower.iloc[-1]); m = float(sma.iloc[-1])
    payload = {"upper": round(u, 5), "mid": round(m, 5), "lower": round(lo, 5)}
    if last > u: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if last < lo: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class BollingerBandsIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
