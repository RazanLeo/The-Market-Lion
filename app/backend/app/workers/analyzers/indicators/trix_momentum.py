"""TRIX momentum = TRIX - TRIX[5 bars ago]. Faster TRIX-based momentum read."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "trix_momentum"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 18
    if len(df) < n * 3 + 15: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    e1 = df["c"].ewm(span=n, adjust=False).mean()
    e2 = e1.ewm(span=n, adjust=False).mean()
    e3 = e2.ewm(span=n, adjust=False).mean()
    trix = 100 * (e3 - e3.shift()) / e3.shift().replace(0, 1e-9)
    mom = trix - trix.shift(5)
    last = float(mom.iloc[-1])
    payload = {"trix_momentum": round(last, 4)}
    if last > 0.05: return AnalyzerResult(CODE, "buy", min(70.0, 40 + abs(last) * 200), WEIGHT_DEFAULT, payload)
    if last < -0.05: return AnalyzerResult(CODE, "sell", min(70.0, 40 + abs(last) * 200), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class TrixMomentumIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
