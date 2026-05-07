"""Stochastic RSI: stochastic of RSI(14) over 14 periods."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "stochastic_rsi"; WEIGHT_DEFAULT = 0.9
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    delta = df["c"].diff()
    up = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    dn = -delta.where(delta < 0, 0).ewm(alpha=1/14, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    sr = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min() + 1e-9)
    last = float(sr.iloc[-1])
    payload = {"stoch_rsi": round(last, 3), "rsi": round(float(rsi.iloc[-1]), 1)}
    if last < 0.2: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last > 0.8: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class StochasticRsiIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
