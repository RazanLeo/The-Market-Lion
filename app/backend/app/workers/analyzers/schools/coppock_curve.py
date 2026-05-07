"""Coppock Curve — WMA(10) of [ROC(14) + ROC(11)]. Buy signal: cross from negative to positive.
Originally for monthly; works on any TF as long-cycle filter.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "coppock_curve"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    roc14 = (c - c.shift(14)) / c.shift(14) * 100
    roc11 = (c - c.shift(11)) / c.shift(11) * 100
    sum_roc = roc14 + roc11
    weights = np.arange(1, 11)
    wma = sum_roc.rolling(10).apply(lambda x: float(np.dot(x, weights) / weights.sum()), raw=False)
    last = float(wma.iloc[-1]); prev = float(wma.iloc[-2])
    cross_up_zero = prev <= 0 and last > 0
    cross_dn_zero = prev >= 0 and last < 0
    rising = last > prev
    payload = {"coppock": round(last, 3), "rising": rising,
               "cross_up_zero": cross_up_zero, "cross_down_zero": cross_dn_zero}
    if cross_up_zero: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if cross_dn_zero: return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if last > 0 and rising: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if last < 0 and not rising: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CoppockCurveAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
