"""Lion Hyperwave — Hyperwave Theory phases via slope-of-slope.

Phase 1 (gradual): EMA20 slope > 0 but flat 2nd derivative.
Phase 2 (steepening): slope-of-slope > 0.
Phase 3 (parabolic): slope >> 0 AND slope-of-slope >> 0 (both at percentile > 80).
Phase 4 (top): slope still positive, slope-of-slope flips negative.
Phase 5 (collapse): slope < 0 with sharp acceleration down.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_hyperwave"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ema20 = df["c"].ewm(span=20, adjust=False).mean()
    slope = ema20.diff()
    slope2 = slope.diff()
    s_now = float(slope.iloc[-1]); s_prev = float(slope.iloc[-5])
    s2_now = float(slope2.iloc[-1])
    s_pct = float((slope.iloc[-100:] <= s_now).sum() / max(len(slope.iloc[-100:]), 1)) if len(slope) >= 100 else 0.5
    s2_pct = float((slope2.iloc[-100:] <= s2_now).sum() / max(len(slope2.iloc[-100:]), 1)) if len(slope2) >= 100 else 0.5
    if s_now > 0 and s2_pct > 0.85 and s_pct > 0.85: phase = 3
    elif s_now > 0 and s2_now > 0: phase = 2
    elif s_now > 0 and s2_now <= 0: phase = 4
    elif s_now < 0 and s2_now < 0: phase = 5
    elif s_now > 0: phase = 1
    else: phase = 0
    payload = {"phase": phase, "slope": round(s_now, 6), "slope2": round(s2_now, 6),
               "slope_percentile": round(s_pct, 2), "slope2_percentile": round(s2_pct, 2)}
    if phase in (1, 2): return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if phase == 3: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, {**payload, "warning": "blow_off_top"})
    if phase == 4: return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    if phase == 5: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionHyperwaveAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
