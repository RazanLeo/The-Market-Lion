"""Williams %R = -100 × (HH14 - C) / (HH14 - LL14)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "williams_r"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 16: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    hh = df["h"].rolling(14).max(); ll = df["l"].rolling(14).min()
    r = -100 * (hh - df["c"]) / (hh - ll + 1e-9)
    last = float(r.iloc[-1])
    payload = {"williams_R": round(last, 1)}
    if last < -80: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last > -20: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class WilliamsRIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
