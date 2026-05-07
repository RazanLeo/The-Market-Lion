"""TRIX = 100 × ROC of Triple-EMA(c, 18). Detect zero-line cross + signal cross."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "trix"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 18
    if len(df) < n * 3 + 10: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    e1 = df["c"].ewm(span=n, adjust=False).mean()
    e2 = e1.ewm(span=n, adjust=False).mean()
    e3 = e2.ewm(span=n, adjust=False).mean()
    trix = 100 * (e3 - e3.shift()) / e3.shift().replace(0, 1e-9)
    sig = trix.rolling(9).mean()
    T, S = float(trix.iloc[-1]), float(sig.iloc[-1])
    Tp, Sp = float(trix.iloc[-2]), float(sig.iloc[-2])
    payload = {"trix": round(T, 4), "signal": round(S, 4)}
    if Tp <= Sp and T > S and T > 0: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if Tp >= Sp and T < S and T < 0: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if T > 0 and T > Tp: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    if T < 0 and T < Tp: return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class TrixIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
