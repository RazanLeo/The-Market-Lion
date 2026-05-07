"""Fibonacci Time Zones — vertical lines at fib-numbered bars from a major low.

Anchor at the most-recent significant low within the last 200 bars.
Fib bar offsets: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144.
A "reaction" is a swing pivot (5-bar fractal) within ±1 bar of an offset.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_time_zones"
WEIGHT_DEFAULT = 0.7
FIB_OFFSETS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-200:] if len(df) > 200 else df
    anchor_idx = int(win["l"].argmin())
    anchor_abs = len(df) - len(win) + anchor_idx
    bars_since_anchor = len(df) - 1 - anchor_abs
    reactions = []
    for off in FIB_OFFSETS:
        target_idx = anchor_abs + off
        if 2 <= target_idx < len(df) - 2:
            lo = max(0, target_idx - 2); hi = min(len(df), target_idx + 3)
            sub = df.iloc[lo:hi]
            is_high = bool(df["h"].iloc[target_idx] == sub["h"].max())
            is_low = bool(df["l"].iloc[target_idx] == sub["l"].min())
            if is_high or is_low:
                reactions.append({"offset": off, "abs_idx": target_idx,
                                  "type": "H" if is_high else "L"})
    distances = [(off, abs(bars_since_anchor - off)) for off in FIB_OFFSETS]
    active_off, active_dist = min(distances, key=lambda x: x[1])
    on_active = active_dist <= 1
    payload = {"anchor_bar": anchor_abs, "bars_since_anchor": bars_since_anchor,
               "reactions": reactions, "active_offset": active_off,
               "distance_to_active": active_dist, "on_active_zone": on_active}
    if not on_active:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    direction = "up" if df["c"].iloc[-1] > df["c"].iloc[-5] else "down"
    if direction == "up":
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, {**payload, "direction": direction})
    return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, {**payload, "direction": direction})


class FibonacciTimeZonesAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
