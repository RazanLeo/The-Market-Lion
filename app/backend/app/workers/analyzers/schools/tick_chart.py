"""Tick Chart School — tick activity proxy via volume / range ratio.

Tick activity per bar ≈ v / range. High ratio = many trades per unit price (active session).
3-bar surge of activity (each > 1.5× rolling avg) = significant interest, signals direction
of last bar.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "tick_chart"
WEIGHT_DEFAULT = 0.6


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    activity = df["v"] / rng
    avg = activity.rolling(20).mean()
    surge = (activity > avg * 1.5)
    last3_surge = int(surge.iloc[-3:].sum())
    direction = float(df["c"].iloc[-1]) - float(df["o"].iloc[-1])
    payload = {"last_activity": round(float(activity.iloc[-1]), 3),
               "avg_20b": round(float(avg.iloc[-1] or 0), 3),
               "last3_surge": last3_surge,
               "bar_direction": "up" if direction > 0 else "down"}
    if last3_surge >= 3 and direction > 0:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last3_surge >= 3 and direction < 0:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class TickChartAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
