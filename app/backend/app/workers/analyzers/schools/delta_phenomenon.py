"""Welles Wilder's Delta Phenomenon — repeating 4-point pivot cycle.

Implementation:
  1. Find last 8 alternating swing pivots (HLHLHLHL or LHLHLHLH).
  2. Measure inter-pivot bar spacing.
  3. If spacings cluster around a constant T (std/mean < 0.3), declare a 4-point Delta cycle.
  4. Project next pivot bar = last_pivot_bar + T.
  5. Phase = which of the 4 points we are on.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "delta_phenomenon"
WEIGHT_DEFAULT = 0.75


def _swings(df: pd.DataFrame, n: int = 4):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H"))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L"))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 120:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 4)
    if len(pivs) < 8:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last8 = pivs[-8:]
    types = "".join(p[1] for p in last8)
    alternating = all(last8[i][1] != last8[i + 1][1] for i in range(7))
    if not alternating:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})
    spacings = [last8[i + 1][0] - last8[i][0] for i in range(7)]
    arr = np.array(spacings, dtype=float)
    coef_var = arr.std() / max(arr.mean(), 1e-9)
    if coef_var > 0.35:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT,
                              {"spacings": spacings, "coef_var": round(coef_var, 3)})
    T = int(round(float(arr.mean())))
    last_pivot_bar = last8[-1][0]
    next_pivot = last_pivot_bar + T
    bars_until = next_pivot - (len(df) - 1)
    last_pivot_kind = last8[-1][1]
    expected_next = "L" if last_pivot_kind == "H" else "H"

    payload = {"period_T": T, "spacings": spacings, "coef_var": round(coef_var, 3),
               "last_pivot_bar": last_pivot_bar, "last_pivot_kind": last_pivot_kind,
               "next_pivot_bar": next_pivot, "bars_until_next_pivot": bars_until,
               "expected_next": expected_next}
    if 0 <= bars_until <= 2:
        # We are at/near the next predicted pivot
        if expected_next == "L":
            return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)


class DeltaPhenomenonAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
