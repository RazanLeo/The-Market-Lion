"""Schaff Trend Cycle. STC applies stochastic oscillator twice on a MACD-like (23,50) indicator."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "schaff_trend_cycle"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    macd = df["c"].ewm(span=23, adjust=False).mean() - df["c"].ewm(span=50, adjust=False).mean()
    ll1 = macd.rolling(10).min(); hh1 = macd.rolling(10).max()
    k1 = 100 * (macd - ll1) / (hh1 - ll1 + 1e-9)
    d1 = k1.ewm(span=3, adjust=False).mean()
    ll2 = d1.rolling(10).min(); hh2 = d1.rolling(10).max()
    k2 = 100 * (d1 - ll2) / (hh2 - ll2 + 1e-9)
    stc = k2.ewm(span=3, adjust=False).mean()
    last = float(stc.iloc[-1])
    payload = {"stc": round(last, 1)}
    if last < 25: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last > 75: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class SchaffTrendCycleIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
