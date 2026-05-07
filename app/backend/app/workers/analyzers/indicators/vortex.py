"""Vortex Indicator. VI+ and VI- over 14 periods."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "vortex"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    vmp = (h - l.shift()).abs(); vmn = (l - h.shift()).abs()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    sum_tr = tr.rolling(14).sum().replace(0, 1e-9)
    vp = vmp.rolling(14).sum() / sum_tr
    vn = vmn.rolling(14).sum() / sum_tr
    P, N = float(vp.iloc[-1]), float(vn.iloc[-1])
    Pp, Np = float(vp.iloc[-2]), float(vn.iloc[-2])
    cross_up = Pp <= Np and P > N
    cross_dn = Pp >= Np and P < N
    payload = {"VI+": round(P, 3), "VI-": round(N, 3)}
    if cross_up: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if cross_dn: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if P - N > 0.1: return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    if N - P > 0.1: return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class VortexIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
