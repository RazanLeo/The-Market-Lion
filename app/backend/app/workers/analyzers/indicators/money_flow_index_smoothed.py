"""Smoothed MFI — MFI then EMA(5)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "money_flow_index_smoothed"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    tp = (df["h"] + df["l"] + df["c"]) / 3
    mf = tp * df["v"].fillna(0)
    pos = mf.where(tp > tp.shift(), 0).rolling(14).sum()
    neg = mf.where(tp < tp.shift(), 0).rolling(14).sum().replace(0, 1e-9)
    mfi = 100 - 100 / (1 + pos / neg)
    smfi = mfi.ewm(span=5, adjust=False).mean()
    last = float(smfi.iloc[-1])
    payload = {"smoothed_mfi": round(last, 1)}
    if last < 25: return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if last > 75: return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class MoneyFlowIndexSmoothedIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
