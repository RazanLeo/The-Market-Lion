"""Turtle Soup (Linda Raschke) — fade false breakouts of 20-day high/low.

Setup: high beats prior 20-day high but closes back inside → SHORT.
       low pierces 20-day low but closes back inside → LONG.
Stop: just beyond the false-break extreme. Profit: previous 20-day midpoint.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "turtle_soup_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win20 = df.iloc[-21:-1]
    h20 = float(win20["h"].max()); l20 = float(win20["l"].min())
    last_h = float(df["h"].iloc[-1]); last_l = float(df["l"].iloc[-1])
    last_c = float(df["c"].iloc[-1])
    short_setup = last_h > h20 and last_c < h20
    long_setup = last_l < l20 and last_c > l20
    mid20 = (h20 + l20) / 2
    payload = {"H20": round(h20, 5), "L20": round(l20, 5), "mid20": round(mid20, 5),
               "short_setup": short_setup, "long_setup": long_setup,
               "stop_short": round(last_h, 5) if short_setup else None,
               "stop_long": round(last_l, 5) if long_setup else None,
               "target": round(mid20, 5)}
    if long_setup: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if short_setup: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class TurtleSoupSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
