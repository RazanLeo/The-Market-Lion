"""ICT Power of Three (PO3) — Asian Accumulation → London Manipulation → NY Distribution.

Steps:
  1. Asian range (00:00-06:00 UTC) = accumulation zone.
  2. London (06:00-12:00 UTC): expects to "manipulate" — sweep above or below the Asian range.
  3. NY (12:00-21:00 UTC): expects to "distribute" — break the opposite direction of manipulation.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "power_of_three_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 96 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    today = df.index[-1].normalize()
    asia = df[(df.index >= today) & (df.index < today + pd.Timedelta(hours=6))]
    london = df[(df.index >= today + pd.Timedelta(hours=6)) & (df.index < today + pd.Timedelta(hours=12))]
    ny = df[df.index >= today + pd.Timedelta(hours=12)]
    if len(asia) < 4 or len(london) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    a_h = float(asia["h"].max()); a_l = float(asia["l"].min())
    l_h = float(london["h"].max()); l_l = float(london["l"].min())
    swept_high = l_h > a_h
    swept_low = l_l < a_l
    cur_phase = "asian_accum" if df.index[-1] < today + pd.Timedelta(hours=6) else \
                "london_manip" if df.index[-1] < today + pd.Timedelta(hours=12) else "ny_distrib"
    expected_distrib = "down" if swept_high else "up" if swept_low else "none"
    last_close = float(df["c"].iloc[-1])
    payload = {"phase": cur_phase, "asian_high": round(a_h, 5), "asian_low": round(a_l, 5),
               "london_swept_high": swept_high, "london_swept_low": swept_low,
               "expected_distribution": expected_distrib}
    if cur_phase == "ny_distrib" and expected_distrib == "down" and last_close < a_h:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if cur_phase == "ny_distrib" and expected_distrib == "up" and last_close > a_l:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class PowerOfThreeSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
