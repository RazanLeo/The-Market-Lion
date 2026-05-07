"""Wilder Parabolic SAR. AF=0.02 step, max 0.20."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "parabolic_sar"; WEIGHT_DEFAULT = 0.9
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l = df["h"], df["l"]
    sar = float(l.iloc[0]); af = 0.02; ep = float(h.iloc[0]); side = 1
    for i in range(1, len(df)):
        ch, cl = float(h.iloc[i]), float(l.iloc[i])
        if side == 1:
            sar += af * (ep - sar)
            if ch > ep: ep = ch; af = min(af + 0.02, 0.20)
            if cl < sar: side = -1; sar = ep; ep = cl; af = 0.02
        else:
            sar -= af * (sar - ep)
            if cl < ep: ep = cl; af = min(af + 0.02, 0.20)
            if ch > sar: side = 1; sar = ep; ep = ch; af = 0.02
    last = float(df["c"].iloc[-1])
    payload = {"sar": round(sar, 5), "side": "long" if side == 1 else "short", "ep": round(ep, 5)}
    if side == 1: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
class ParabolicSarIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
