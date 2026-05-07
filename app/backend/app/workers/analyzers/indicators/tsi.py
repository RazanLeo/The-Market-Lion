"""True Strength Index. Double-smooth (EMA25 then EMA13) of (price change) / abs(price change)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "tsi"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pc = df["c"].diff()
    num = pc.ewm(span=25, adjust=False).mean().ewm(span=13, adjust=False).mean()
    den = pc.abs().ewm(span=25, adjust=False).mean().ewm(span=13, adjust=False).mean()
    tsi = 100 * num / den.replace(0, 1e-9)
    last = float(tsi.iloc[-1]); prev = float(tsi.iloc[-2])
    payload = {"tsi": round(last, 2)}
    if last > 0 and prev <= 0: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last < 0 and prev >= 0: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if last > 25: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if last < -25: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class TsiIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
