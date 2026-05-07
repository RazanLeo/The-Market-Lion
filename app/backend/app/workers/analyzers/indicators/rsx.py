"""Jurik RSX (smoothed RSI). Approximation: 4 stages of Jurik smoothing on RSI(14)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "rsx"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    delta = df["c"].diff()
    up = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    dn = -delta.where(delta < 0, 0).ewm(alpha=1/14, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    rsx = rsi.ewm(span=4, adjust=False).mean().ewm(span=4, adjust=False).mean().ewm(span=4, adjust=False).mean()
    last = float(rsx.iloc[-1])
    payload = {"rsx": round(last, 1)}
    if last < 30: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last > 70: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class RsxIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
