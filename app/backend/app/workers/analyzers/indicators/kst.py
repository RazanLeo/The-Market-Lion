"""Pring Know Sure Thing — weighted sum of smoothed ROCs (10,15,20,30 periods)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "kst"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    rocs = []
    for p, s, w in [(10, 10, 1), (15, 10, 2), (20, 10, 3), (30, 15, 4)]:
        rocs.append(((c - c.shift(p)) / c.shift(p) * 100).rolling(s).mean() * w)
    kst = sum(rocs)
    sig = kst.rolling(9).mean()
    K, S = float(kst.iloc[-1]), float(sig.iloc[-1])
    Kp, Sp = float(kst.iloc[-2]), float(sig.iloc[-2])
    cross_up = Kp <= Sp and K > S
    cross_dn = Kp >= Sp and K < S
    payload = {"kst": round(K, 2), "signal": round(S, 2)}
    if cross_up: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if cross_dn: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if K > 0: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
class KstIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
