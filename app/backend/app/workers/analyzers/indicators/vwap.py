"""VWAP — anchored at session start. Σ(TP×V) / Σ V."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "vwap"; WEIGHT_DEFAULT = 0.95
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    if isinstance(df.index, pd.DatetimeIndex):
        today = df.index[-1].normalize()
        sub = df[df.index >= today]
        if len(sub) < 5: sub = df.iloc[-96:]
    else:
        sub = df.iloc[-96:]
    tp = (sub["h"] + sub["l"] + sub["c"]) / 3
    v = sub["v"].fillna(1)
    vwap = (tp * v).cumsum() / v.cumsum().replace(0, 1e-9)
    last = float(df["c"].iloc[-1]); vw = float(vwap.iloc[-1])
    payload = {"vwap": round(vw, 5)}
    if last > vw * 1.001: return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if last < vw * 0.999: return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class VwapIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
