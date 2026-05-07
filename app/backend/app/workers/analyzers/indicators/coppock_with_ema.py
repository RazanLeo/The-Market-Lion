"""Coppock Curve with EMA filter — Pring's WMA(10) of (ROC14 + ROC11), filtered by 12-EMA.

Standard Coppock signals long-term buys when crossing zero from below. Adding an EMA
filter (Coppock vs its 12-EMA) reduces whipsaws. Buy when Coppock > EMA(Coppock,12)
AND Coppock crosses 0 upward.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "coppock_with_ema"
WEIGHT_DEFAULT = 0.75


def _wma(s: pd.Series, n: int) -> pd.Series:
    weights = pd.Series(range(1, n + 1)).astype(float)
    return s.rolling(n).apply(lambda x: float((x * weights.values).sum() / weights.sum()), raw=True)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    roc14 = (c - c.shift(14)) / c.shift(14) * 100
    roc11 = (c - c.shift(11)) / c.shift(11) * 100
    coppock = _wma(roc14 + roc11, 10)
    coppock_ema = coppock.ewm(span=12, adjust=False).mean()
    last = float(coppock.iloc[-1] or 0); prev = float(coppock.iloc[-2] or 0)
    last_ema = float(coppock_ema.iloc[-1] or 0); prev_ema = float(coppock_ema.iloc[-2] or 0)
    cross_up = prev <= 0 < last
    cross_dn = prev >= 0 > last
    above_ema = last > last_ema
    payload = {"coppock": round(last, 3), "coppock_ema": round(last_ema, 3),
               "above_filter": above_ema, "zero_cross_up": cross_up, "zero_cross_dn": cross_dn}
    if cross_up and above_ema:
        return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if cross_dn and not above_ema:
        return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    if last > last_ema and prev <= prev_ema:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if last < last_ema and prev >= prev_ema:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CoppockWithEmaAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
