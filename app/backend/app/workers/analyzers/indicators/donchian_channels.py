"""Donchian Channels (n=20). Upper = highest_high(n); Lower = lowest_low(n); Mid = avg."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "donchian_channels"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    upper = df["h"].rolling(20).max(); lower = df["l"].rolling(20).min()
    mid = (upper + lower) / 2
    last = float(df["c"].iloc[-1])
    u = float(upper.iloc[-1]); lo = float(lower.iloc[-1]); m = float(mid.iloc[-1])
    payload = {"upper": round(u, 5), "lower": round(lo, 5), "mid": round(m, 5)}
    if last >= u * 0.999: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last <= lo * 1.001: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if last > m: return AnalyzerResult(CODE, "buy", 35, WEIGHT_DEFAULT, payload)
    if last < m: return AnalyzerResult(CODE, "sell", 35, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class DonchianChannelsIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
