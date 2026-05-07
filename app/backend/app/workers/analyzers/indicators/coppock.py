"""Coppock Curve = WMA(10) of ROC(14)+ROC(11)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "coppock"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    roc14 = (c - c.shift(14)) / c.shift(14) * 100
    roc11 = (c - c.shift(11)) / c.shift(11) * 100
    sum_roc = (roc14 + roc11)
    weights = np.arange(1, 11)
    wma = sum_roc.rolling(10).apply(lambda x: float(np.dot(x, weights) / weights.sum()), raw=True)
    last = float(wma.iloc[-1]); prev = float(wma.iloc[-2])
    cross_up = prev <= 0 and last > 0
    cross_dn = prev >= 0 and last < 0
    payload = {"coppock": round(last, 3)}
    if cross_up: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if cross_dn: return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if last > 0 and last > prev: return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    if last < 0 and last < prev: return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class CoppockIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
