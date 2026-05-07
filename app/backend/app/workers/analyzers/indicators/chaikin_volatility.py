"""Chaikin Volatility = % change in EMA10(H-L) over 10 periods."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "chaikin_volatility"; WEIGHT_DEFAULT = 0.55
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    spread = (df["h"] - df["l"]).ewm(span=10, adjust=False).mean()
    cv = (spread - spread.shift(10)) / spread.shift(10).replace(0, 1e-9) * 100
    last = float(cv.iloc[-1])
    payload = {"chaikin_volatility_pct": round(last, 2)}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class ChaikinVolatilityIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
