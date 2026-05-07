"""CCI = (TP - SMA20(TP)) / (0.015 × Mean Deviation). TP = (H+L+C)/3."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "cci"; WEIGHT_DEFAULT = 0.9
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    tp = (df["h"] + df["l"] + df["c"]) / 3
    sma = tp.rolling(20).mean()
    md = (tp - sma).abs().rolling(20).mean()
    cci = (tp - sma) / (0.015 * md.replace(0, 1e-9))
    last = float(cci.iloc[-1])
    payload = {"cci": round(last, 1)}
    if last < -100: return AnalyzerResult(CODE, "buy", min(75.0, 45 + abs(last) * 0.15), WEIGHT_DEFAULT, payload)
    if last > 100: return AnalyzerResult(CODE, "sell", min(75.0, 45 + abs(last) * 0.15), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class CciIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
