"""Bullish Percent Index (BPI proxy) — % of bars that closed up over rolling N.

Standard BPI is a market-breadth indicator (% of stocks on P&F buy signal); here we
adapt to a single-instrument proxy: % of bars in last 50 with c > c.shift(1). BPI
above 70 = overbought, below 30 = oversold. Cross 30 → 50 = buy, cross 70 → 50 = sell.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "bullish_percent_index"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    up = (df["c"] > df["c"].shift(1)).astype(float)
    bpi = up.rolling(50).mean() * 100
    last = float(bpi.iloc[-1])
    prev = float(bpi.iloc[-2])
    payload = {"bpi": round(last, 2), "bpi_prev": round(prev, 2),
               "regime": "overbought" if last > 70 else "oversold" if last < 30 else "neutral"}
    if prev < 30 and last >= 30:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if prev > 70 and last <= 70:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if last < 25:
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if last > 75:
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class BullishPercentIndexAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
