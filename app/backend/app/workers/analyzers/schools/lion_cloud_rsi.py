"""Lion Cloud RSI — multi-period RSI cloud (7 / 14 / 28).

Bullish: all three RSIs > 50 AND RSI(7) on top.
Bearish: all three < 50 AND RSI(7) on bottom.
Cloud thickness = RSI(7) - RSI(28). Larger thickness = stronger momentum.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_cloud_rsi"
WEIGHT_DEFAULT = 0.95


def _rsi(c: pd.Series, p: int) -> pd.Series:
    delta = c.diff()
    up = delta.where(delta > 0, 0).ewm(alpha=1 / p, adjust=False).mean()
    dn = -delta.where(delta < 0, 0).ewm(alpha=1 / p, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    r7 = _rsi(c, 7); r14 = _rsi(c, 14); r28 = _rsi(c, 28)
    a, b, c_ = float(r7.iloc[-1]), float(r14.iloc[-1]), float(r28.iloc[-1])
    bull = a > 50 and b > 50 and c_ > 50 and a > b > c_
    bear = a < 50 and b < 50 and c_ < 50 and a < b < c_
    thickness = a - c_
    payload = {"rsi7": round(a, 1), "rsi14": round(b, 1), "rsi28": round(c_, 1),
               "thickness": round(thickness, 1),
               "cloud_color": "green" if bull else "red" if bear else "mixed"}
    if bull: return AnalyzerResult(CODE, "buy", min(85.0, 50 + abs(thickness)), WEIGHT_DEFAULT, payload)
    if bear: return AnalyzerResult(CODE, "sell", min(85.0, 50 + abs(thickness)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionCloudRsiAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
