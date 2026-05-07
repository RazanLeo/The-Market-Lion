"""Deviation Envelope (percent envelope around SMA20 ± 2.5%)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "deviation_envelope"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sma = df["c"].rolling(20).mean()
    upper = sma * 1.025; lower = sma * 0.975
    last = float(df["c"].iloc[-1]); u = float(upper.iloc[-1]); l = float(lower.iloc[-1])
    payload = {"upper": round(u, 5), "lower": round(l, 5), "last": round(last, 5)}
    if last < l: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last > u: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class DeviationEnvelopeIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
