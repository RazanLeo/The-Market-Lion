"""Stochastic %K(14) and %D(3)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "stochastic"; WEIGHT_DEFAULT = 0.9
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ll = df["l"].rolling(14).min(); hh = df["h"].rolling(14).max()
    k = 100 * (df["c"] - ll) / (hh - ll + 1e-9)
    d = k.rolling(3).mean()
    K, D = float(k.iloc[-1]), float(d.iloc[-1])
    Kp, Dp = float(k.iloc[-2]), float(d.iloc[-2])
    payload = {"K": round(K, 1), "D": round(D, 1)}
    if K < 20 and Kp <= Dp and K > D: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if K > 80 and Kp >= Dp and K < D: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if K < 20: return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    if K > 80: return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class StochasticIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
