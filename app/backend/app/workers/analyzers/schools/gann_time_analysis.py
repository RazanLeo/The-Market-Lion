"""Gann Time Analysis — major-pivot anniversaries at 30/60/90/120/180/360 bars forward.

Find significant lows and highs over last 400 bars (or all available). For each, project
forward by Gann's time intervals and check if current bar is at one of those projections.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "gann_time_analysis"
WEIGHT_DEFAULT = 0.7
INTERVALS = [30, 60, 90, 120, 180, 270, 360]


def _major_pivots(df: pd.DataFrame, n: int = 8):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _major_pivots(df, 8)
    if not pivs:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_idx = len(df) - 1
    hits = []
    for (idx, kind, _) in pivs:
        for iv in INTERVALS:
            target = idx + iv
            if abs(target - last_idx) <= 1:
                hits.append({"source_bar": idx, "kind": kind, "interval": iv})
    payload = {"pivot_count": len(pivs), "anniversary_hits": hits}
    if not hits:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    # Direction inferred from most recent direction
    direction_up = float(df["c"].iloc[-1]) > float(df["c"].iloc[-10])
    score = min(70.0, 40 + len(hits) * 10)
    if direction_up:
        return AnalyzerResult(CODE, "sell", score, WEIGHT_DEFAULT, payload)  # anniversary often = reversal
    return AnalyzerResult(CODE, "buy", score, WEIGHT_DEFAULT, payload)


class GannTimeAnalysisAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
