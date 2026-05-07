"""Pivot HL — recent swing-based pivot levels.

Identifies the most recent swing-high (H) and swing-low (L) using a 5-bar fractal,
then computes proximity to last close. Bullish if close near pivot-low (rebound),
bearish if close near pivot-high (rejection).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "pivot_hl"
WEIGHT_DEFAULT = 0.85


def _swing_pivots(df: pd.DataFrame, n: int = 2):
    highs, lows = [], []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            highs.append((i, float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            lows.append((i, float(df["l"].iloc[i])))
    return highs, lows


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    highs, lows = _swing_pivots(df, 2)
    if not highs or not lows:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_h_idx, last_h = highs[-1]
    last_l_idx, last_l = lows[-1]
    last_c = float(df["c"].iloc[-1])
    rng = last_h - last_l + 1e-9
    pos = (last_c - last_l) / rng
    payload = {"last_swing_high": last_h, "last_swing_low": last_l,
               "h_bar": last_h_idx, "l_bar": last_l_idx,
               "position_in_range": round(pos, 3)}
    if pos < 0.25:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if pos > 0.75:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class PivotHlAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
