"""Hurst Cycles — multi-cycle decomposition using a centered moving-average filter bank.

Hurst's principle of synchronicity: nested cycles aligned at troughs.
  Short cycle: residuals from CMA(8)
  Medium cycle: residuals from CMA(20)
  Long cycle: residuals from CMA(40)

A "stack buy" = all 3 cycles in their first half (rising) AND short cycle just made a local minimum.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "hurst_cycles"
WEIGHT_DEFAULT = 0.9


def _cma(s: pd.Series, w: int) -> pd.Series:
    return s.rolling(w, center=True).mean()


def _phase(residual: pd.Series, period: int) -> str:
    win = residual.iloc[-period * 2:].dropna()
    if len(win) < period:
        return "unknown"
    last_low = int(np.nanargmin(win.to_numpy()))
    bars_since = len(win) - 1 - last_low
    pos = bars_since / period
    if pos < 0.5: return "rising"
    if pos < 0.9: return "topping"
    return "falling"


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 120:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    res_s = c - _cma(c, 8)
    res_m = c - _cma(c, 20)
    res_l = c - _cma(c, 40)
    p_s = _phase(res_s, 8)
    p_m = _phase(res_m, 20)
    p_l = _phase(res_l, 40)
    rising = sum(1 for p in (p_s, p_m, p_l) if p == "rising")
    falling = sum(1 for p in (p_s, p_m, p_l) if p == "falling")
    payload = {"short": p_s, "medium": p_m, "long": p_l,
               "rising_count": rising, "falling_count": falling}
    if rising >= 2 and falling == 0:
        return AnalyzerResult(CODE, "buy", min(80.0, 40 + rising * 15), WEIGHT_DEFAULT, payload)
    if falling >= 2 and rising == 0:
        return AnalyzerResult(CODE, "sell", min(80.0, 40 + falling * 15), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class HurstCyclesAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
