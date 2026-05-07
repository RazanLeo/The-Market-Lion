"""Lion Overflow Oscillator — ROC(10) percentile rank.

Rank current ROC(10) within last 100 ROC values. Rank > 95 = overbought exhaustion
(sell), rank < 5 = oversold exhaustion (buy). Mean-reversion oscillator.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_overflow_oscillator"
WEIGHT_DEFAULT = 0.8


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 120:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    roc = (df["c"] - df["c"].shift(10)) / df["c"].shift(10) * 100
    win = roc.iloc[-100:].dropna()
    cur = float(roc.iloc[-1]) if not pd.isna(roc.iloc[-1]) else 0
    rank = float((win <= cur).sum() / len(win) * 100) if len(win) else 50
    payload = {"roc10": round(cur, 3), "percentile_rank": round(rank, 1),
               "overflow_top": rank > 95, "overflow_bottom": rank < 5}
    if rank > 95:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if rank < 5:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if rank > 90:
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    if rank < 10:
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionOverflowOscillatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
