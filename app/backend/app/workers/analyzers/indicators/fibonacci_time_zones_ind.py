"""Fibonacci Time Zones (indicator) — vertical lines at fib bar counts from anchor.

Anchor = significant low. Vertical lines at offsets 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144.
Detects whether current bar coincides (±1 bar) with a fib zone. If so, expects a turning
point. Direction inferred from short-term momentum.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_time_zones_ind"
WEIGHT_DEFAULT = 0.65
FIB_OFFSETS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-200:] if len(df) > 200 else df
    a_i_rel = int(win["l"].argmin())
    a_i_abs = len(df) - len(win) + a_i_rel
    bars_since = len(df) - 1 - a_i_abs
    distances = [(off, abs(bars_since - off)) for off in FIB_OFFSETS]
    nearest_off, nearest_dist = min(distances, key=lambda x: x[1])
    on_zone = nearest_dist <= 1
    momentum = float(df["c"].iloc[-1]) - float(df["c"].iloc[-3])
    payload = {"anchor_bar": int(a_i_abs), "bars_since_anchor": int(bars_since),
               "nearest_fib_offset": nearest_off, "distance": int(nearest_dist),
               "on_zone": on_zone}
    if not on_zone:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    if momentum > 0:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)  # turn-point fade
    return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)


class FibonacciTimeZonesIndAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
