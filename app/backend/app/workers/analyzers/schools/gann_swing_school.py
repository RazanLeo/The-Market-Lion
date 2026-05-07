"""Gann Swing Chart — direction changes only on a 2-bar reversal (close beyond 2-bar high/low).

Construct an "Up Swing" while each new bar's high exceeds the prior swing-high.
Switch to "Down Swing" only when close < min(low[t-1], low[t-2]).
Track swing duration (bars in current direction).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "gann_swing_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    direction = 0  # +1 up, -1 down, 0 unknown
    swing_high = float(df["h"].iloc[0]); swing_low = float(df["l"].iloc[0])
    duration = 1
    for i in range(2, len(df)):
        h_i = float(df["h"].iloc[i]); l_i = float(df["l"].iloc[i]); c_i = float(df["c"].iloc[i])
        prev_l_min2 = min(float(df["l"].iloc[i - 1]), float(df["l"].iloc[i - 2]))
        prev_h_max2 = max(float(df["h"].iloc[i - 1]), float(df["h"].iloc[i - 2]))
        if direction in (0, 1):
            if h_i > swing_high:
                swing_high = h_i; duration += 1; direction = 1
            elif c_i < prev_l_min2:
                direction = -1; duration = 1; swing_low = l_i
        else:  # direction == -1
            if l_i < swing_low:
                swing_low = l_i; duration += 1
            elif c_i > prev_h_max2:
                direction = 1; duration = 1; swing_high = h_i

    payload = {"direction": "up" if direction == 1 else "down" if direction == -1 else "unknown",
               "swing_high": round(swing_high, 5), "swing_low": round(swing_low, 5),
               "duration_bars": duration}
    if direction == 1 and duration >= 5:
        return AnalyzerResult(CODE, "buy", min(75.0, 40 + duration), WEIGHT_DEFAULT, payload)
    if direction == -1 and duration >= 5:
        return AnalyzerResult(CODE, "sell", min(75.0, 40 + duration), WEIGHT_DEFAULT, payload)
    if direction == 1: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    if direction == -1: return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class GannSwingSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
