"""Fibonacci Arcs — semi-circles at fib radii from anchor.

Anchor at the lowest low in last 100 bars. Radius_R = distance from anchor to highest
high. Fib arcs at 0.382R, 0.5R, 0.618R. Tests whether current bar's distance from the
anchor in (time, price) is intersecting a fib arc — signaling potential support/resistance.
"""
from __future__ import annotations
import math
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_arcs"
WEIGHT_DEFAULT = 0.55
ARC_RATIOS = [0.382, 0.5, 0.618]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-100:] if len(df) > 100 else df
    a_i = int(win["l"].argmin()); a_p = float(win["l"].iloc[a_i])
    after = win.iloc[a_i + 1:]
    if len(after) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    b_i_rel = int(after["h"].argmax())
    b_p = float(after["h"].iloc[b_i_rel])
    radius = b_p - a_p
    if radius <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_c = float(df["c"].iloc[-1])
    cur_t = len(df) - 1 - (len(df) - len(win) + a_i)  # bars since anchor
    cur_d = math.sqrt((last_c - a_p) ** 2 + (cur_t * (radius / max(a_i + b_i_rel + 1, 1))) ** 2)
    arcs = {f"arc_{r}": round(r * radius, 5) for r in ARC_RATIOS}
    nearest = min(ARC_RATIOS, key=lambda r: abs(cur_d - r * radius))
    on_arc = abs(cur_d - nearest * radius) < radius * 0.05
    payload = {"anchor_low": a_p, "high_b": b_p, "radius": round(radius, 5),
               "arcs": arcs, "current_distance": round(cur_d, 5),
               "nearest_arc": nearest, "on_arc": on_arc}
    if on_arc and nearest >= 0.5 and last_c > float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if on_arc and nearest >= 0.5 and last_c < float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FibonacciArcsAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
