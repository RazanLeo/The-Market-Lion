"""Chande Momentum Oscillator = 100 × (sumUp - sumDown) / (sumUp + sumDown). Range -100..+100."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "chande_momentum"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    diff = df["c"].diff()
    up = diff.where(diff > 0, 0).rolling(14).sum()
    dn = -diff.where(diff < 0, 0).rolling(14).sum()
    cmo = 100 * (up - dn) / (up + dn + 1e-9)
    last = float(cmo.iloc[-1])
    payload = {"cmo": round(last, 1)}
    if last > 50: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last < -50: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class ChandeMomentumIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
