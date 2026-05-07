"""VWAP School — Anchored VWAP from session start + ±1σ/±2σ bands.

VWAP = Σ(typical_price × volume) / Σ volume.
Anchor = UTC midnight of current day.
σ = standard deviation of (typical_price - VWAP) weighted by volume.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "vwap_school"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    if not isinstance(df.index, pd.DatetimeIndex):
        anchor = max(0, len(df) - 96)
        sub = df.iloc[anchor:]
    else:
        today = df.index[-1].normalize()
        sub = df[df.index >= today]
        if len(sub) < 5: sub = df.iloc[-96:]
    tp = (sub["h"] + sub["l"] + sub["c"]) / 3
    v = sub["v"].fillna(1)
    cum_pv = (tp * v).cumsum()
    cum_v = v.cumsum().replace(0, 1e-9)
    vwap_series = cum_pv / cum_v
    vwap = float(vwap_series.iloc[-1])
    # Volume-weighted variance
    weighted_var = ((tp - vwap_series) ** 2 * v).cumsum() / cum_v
    sigma = float(np.sqrt(max(weighted_var.iloc[-1], 0)))
    last = float(df["c"].iloc[-1])
    upper1 = vwap + sigma; lower1 = vwap - sigma
    upper2 = vwap + 2 * sigma; lower2 = vwap - 2 * sigma
    payload = {"vwap": round(vwap, 5), "sigma": round(sigma, 5),
               "upper_1sigma": round(upper1, 5), "lower_1sigma": round(lower1, 5),
               "upper_2sigma": round(upper2, 5), "lower_2sigma": round(lower2, 5),
               "last_close": round(last, 5)}
    if last > upper2: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if last < lower2: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last > upper1 and last > vwap_series.iloc[-2]:  # walking band
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if last < lower1 and last < vwap_series.iloc[-2]:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    if abs(last - vwap) / max(sigma, 1e-9) < 0.3:
        # mean-reverting at VWAP test: bias = trend slope
        slope = float(vwap_series.iloc[-1] - vwap_series.iloc[-10])
        if slope > 0: return AnalyzerResult(CODE, "buy", 35, WEIGHT_DEFAULT, payload)
        if slope < 0: return AnalyzerResult(CODE, "sell", 35, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VwapSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
