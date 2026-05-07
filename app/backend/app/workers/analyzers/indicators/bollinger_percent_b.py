"""Bollinger %B = (price - lower) / (upper - lower)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "bollinger_percent_b"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sma = df["c"].rolling(20).mean(); sd = df["c"].rolling(20).std()
    upper = sma + 2 * sd; lower = sma - 2 * sd
    pb = (df["c"] - lower) / (upper - lower + 1e-9)
    last = float(pb.iloc[-1])
    payload = {"%B": round(last, 3)}
    if last < 0: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last > 1: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if last < 0.2: return AnalyzerResult(CODE, "buy", 35, WEIGHT_DEFAULT, payload)
    if last > 0.8: return AnalyzerResult(CODE, "sell", 35, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class BollingerPercentBIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
