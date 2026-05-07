"""Lion Overflow — extreme momentum break detection.

Compute ROC(10). If |ROC| exceeds the 95th percentile of last 100 bars,
flag overflow. Direction = sign of ROC.
At extreme overflow, expect reversal (mean-reversion target).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_overflow"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 120:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    roc10 = (c - c.shift(10)) / c.shift(10) * 100
    last = float(roc10.iloc[-1])
    win = roc10.iloc[-100:].dropna()
    if len(win) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    p95 = float(np.percentile(win.abs(), 95))
    overflow = abs(last) > p95
    direction = "up" if last > 0 else "down"
    payload = {"roc10": round(last, 2), "p95_abs": round(p95, 2),
               "overflow": overflow, "direction": direction}
    if not overflow:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    # contrarian on extreme
    if direction == "up":
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, {**payload, "warning": "overbought_extreme"})
    return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, {**payload, "warning": "oversold_extreme"})


class LionOverflowAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
