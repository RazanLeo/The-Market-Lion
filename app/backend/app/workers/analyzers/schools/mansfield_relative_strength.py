"""Mansfield Relative Strength — RS Rating derived from 200-period SMA ratio, smoothed 13 periods.

Mansfield formula: RS = (price/SMA_long - 1) × 100, smoothed by 13-period EMA.
Above 0 = leader; below 0 = laggard.
RS direction (rising vs falling) is the actionable trigger.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "mansfield_relative_strength"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 220:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    sma200 = c.rolling(200).mean()
    rs_raw = (c / sma200 - 1) * 100
    rs = rs_raw.ewm(span=13, adjust=False).mean()
    last_rs = float(rs.iloc[-1])
    rs_slope = float(rs.iloc[-1] - rs.iloc[-10]) / 10
    payload = {"rs_rating": round(last_rs, 2), "rs_slope_per_bar": round(rs_slope, 4)}
    if last_rs > 0 and rs_slope > 0:
        return AnalyzerResult(CODE, "buy", min(80.0, 45 + abs(last_rs) * 2), WEIGHT_DEFAULT, payload)
    if last_rs < 0 and rs_slope < 0:
        return AnalyzerResult(CODE, "sell", min(80.0, 45 + abs(last_rs) * 2), WEIGHT_DEFAULT, payload)
    if last_rs > 0 and rs_slope < 0:
        return AnalyzerResult(CODE, "sell", 35, WEIGHT_DEFAULT, payload)  # leadership weakening
    if last_rs < 0 and rs_slope > 0:
        return AnalyzerResult(CODE, "buy", 35, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MansfieldRelativeStrengthAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
