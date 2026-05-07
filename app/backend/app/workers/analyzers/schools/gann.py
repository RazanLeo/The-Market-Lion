"""Gann Theory — Angles (1×8 … 8×1), Square of Nine key levels, time-price relationships.

The Gann angles are computed from the most-recent significant pivot (swing low for bull
context, swing high for bear) using a unit slope = 1 unit of price per unit of time.
We measure 1 unit of time as 1 bar and 1 unit of price as 1×ATR(14)/2 (a common scaling).

Angles supported:  1×8, 1×4, 1×2, 1×1, 2×1, 4×1, 8×1
Square of 9: progressive sqrt levels around pivot price.
"""
from __future__ import annotations
import math
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "gann"
WEIGHT_DEFAULT = 1.0


def _square_of_nine(price: float, n: int = 8) -> list[float]:
    """Return key SQ9 levels above the pivot."""
    base = math.sqrt(price)
    levels = []
    for k in range(1, n + 1):
        for inc in (0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0):
            up = (base + k * inc) ** 2
            down = (base - k * inc) ** 2 if base - k * inc > 0 else None
            levels.append(round(up, 5))
            if down: levels.append(round(down, 5))
    return sorted(set(levels))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    win = df.iloc[-60:]
    h_idx = int(win["h"].argmax()); l_idx = int(win["l"].argmin())
    pivot_price = float(win["l"].iloc[l_idx]) if l_idx > h_idx else float(win["h"].iloc[h_idx])
    bullish_pivot = l_idx > h_idx
    bars_since = len(df) - (df.index.get_loc(win.index[l_idx if bullish_pivot else h_idx]))
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 0)
    unit_price = atr / 2.0
    if unit_price <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    angles = {
        "1x8": 1 / 8, "1x4": 1 / 4, "1x2": 1 / 2, "1x1": 1,
        "2x1": 2, "4x1": 4, "8x1": 8,
    }
    angle_levels = {}
    for name, slope in angles.items():
        if bullish_pivot:
            angle_levels[name] = pivot_price + bars_since * unit_price * slope
        else:
            angle_levels[name] = pivot_price - bars_since * unit_price * slope

    last = float(df["c"].iloc[-1])
    nearest_angle, nearest_dist = None, float("inf")
    for name, lvl in angle_levels.items():
        d = abs(last - lvl)
        if d < nearest_dist:
            nearest_dist = d; nearest_angle = name

    sq9 = _square_of_nine(pivot_price, n=4)
    nearest_sq9 = min(sq9, key=lambda x: abs(x - last))
    sq9_dist = abs(nearest_sq9 - last)

    on_1x1 = abs(last - angle_levels["1x1"]) < unit_price * 0.5

    payload = {
        "pivot": round(pivot_price, 5), "bullish_pivot": bullish_pivot,
        "bars_since_pivot": int(bars_since),
        "angles": {k: round(v, 5) for k, v in angle_levels.items()},
        "nearest_angle": nearest_angle,
        "nearest_angle_dist_units": round(nearest_dist / unit_price, 2),
        "on_1x1": on_1x1,
        "sq9_nearest": round(nearest_sq9, 5),
        "sq9_dist_units": round(sq9_dist / unit_price, 2),
    }

    score = 0.0
    if bullish_pivot:
        if last > angle_levels["1x1"]: score += 20
        if last > angle_levels["2x1"]: score += 10
        if last < angle_levels["1x2"]: score -= 15
    else:
        if last < angle_levels["1x1"]: score -= 20
        if last < angle_levels["2x1"]: score -= 10
        if last > angle_levels["1x2"]: score += 15
    if on_1x1: score *= 1.2
    if sq9_dist < unit_price * 0.3:  # near key SQ9 level
        score += 8 if bullish_pivot else -8

    if score >= 15:
        return AnalyzerResult(CODE, "buy", min(80.0, 45 + score), WEIGHT_DEFAULT, payload)
    if score <= -15:
        return AnalyzerResult(CODE, "sell", min(80.0, 45 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class GannAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
