"""Awesome Oscillator: SMA(median, 5) - SMA(median, 34). median = (h+l)/2."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "awesome_oscillator"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    median = (df["h"] + df["l"]) / 2
    ao = median.rolling(5).mean() - median.rolling(34).mean()
    last = float(ao.iloc[-1]); prev = float(ao.iloc[-2])
    payload = {"ao": round(last, 5)}
    if last > 0 and prev <= 0: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last < 0 and prev >= 0: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if last > 0 and last > prev: return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    if last < 0 and last < prev: return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class AwesomeOscillatorIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
