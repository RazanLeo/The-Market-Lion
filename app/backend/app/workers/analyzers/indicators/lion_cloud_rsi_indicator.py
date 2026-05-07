"""Lion Cloud RSI — multi-period RSI cloud (7/14/28).

Plots three RSIs as a "cloud": green when fast > slow (uptrend regime), red when fast
< slow (downtrend). Cloud thickness = (RSI7 - RSI28) magnitude.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_cloud_rsi_indicator"
WEIGHT_DEFAULT = 0.8


def _rsi(c, n):
    diff = c.diff()
    up = diff.clip(lower=0); dn = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / (ad + 1e-9))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    r7 = float(_rsi(df["c"], 7).iloc[-1])
    r14 = float(_rsi(df["c"], 14).iloc[-1])
    r28 = float(_rsi(df["c"], 28).iloc[-1])
    color = "green" if r7 > r14 > r28 else "red" if r7 < r14 < r28 else "mixed"
    thickness = abs(r7 - r28)
    bull_stack = r7 > r14 > r28 and r14 > 50
    bear_stack = r7 < r14 < r28 and r14 < 50
    payload = {"rsi7": round(r7, 1), "rsi14": round(r14, 1), "rsi28": round(r28, 1),
               "cloud_color": color, "cloud_thickness": round(thickness, 1),
               "bull_stack": bull_stack, "bear_stack": bear_stack}
    if bull_stack and thickness > 5:
        return AnalyzerResult(CODE, "buy", min(80, 50 + thickness), WEIGHT_DEFAULT, payload)
    if bear_stack and thickness > 5:
        return AnalyzerResult(CODE, "sell", min(80, 50 + thickness), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionCloudRsiIndicatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
