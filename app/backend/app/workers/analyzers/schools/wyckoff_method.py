"""Wyckoff Method — Three Laws scoring (Effort vs Result, Cause vs Effect, Supply vs Demand).

Distinct from wyckoff_school (phase detection): focuses on the three laws as a single
composite score.
  • Effort vs Result: high vol but small price change = stealth absorption
  • Cause vs Effect: range-width × time (cause) projects future move (effect)
  • Supply vs Demand: net signed volume over rolling 30 bars
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "wyckoff_method"
WEIGHT_DEFAULT = 1.05


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    vol_avg = float(df["v"].rolling(30).mean().iloc[-1] or 0)
    if atr <= 0 or vol_avg <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last5 = df.iloc[-5:]
    avg_vol_last5 = float(last5["v"].mean())
    avg_range_last5 = float((last5["h"] - last5["l"]).mean())
    effort_high_result_low = (avg_vol_last5 > vol_avg * 1.3) and (avg_range_last5 < atr * 0.8)
    # Cause: trading range width and bars in range
    win = df.iloc[-30:]
    range_width = float(win["h"].max() - win["l"].min())
    bars_in_range = int(((win["h"] < win["h"].max() * 1.005) & (win["l"] > win["l"].min() * 0.995)).sum())
    cause = range_width * bars_in_range / max(atr * 30, 1e-9)
    # Supply vs Demand
    sign = np.sign(df["c"] - df["c"].shift(1)).fillna(0)
    net_signed_vol = float((sign * df["v"]).iloc[-30:].sum())
    sd_bias = "demand" if net_signed_vol > 0 else "supply"
    payload = {"effort_vs_result_stealth": effort_high_result_low,
               "cause_index": round(cause, 2), "bars_in_range_30": bars_in_range,
               "net_signed_vol_30": round(net_signed_vol, 2),
               "supply_demand_bias": sd_bias}
    score = 0
    if effort_high_result_low: score += 1  # stealth absorption — pre-breakout
    if cause > 1.5: score += 1  # large cause built
    if sd_bias == "demand": score += 1
    if sd_bias == "supply": score -= 1
    if effort_high_result_low and sd_bias == "demand":
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if effort_high_result_low and sd_bias == "supply":
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if score >= 2:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if score <= -1:
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class WyckoffMethodAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
