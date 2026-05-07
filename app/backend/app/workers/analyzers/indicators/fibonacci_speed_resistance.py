"""Fibonacci Speed Resistance — speed lines at 1/3 and 2/3 of price leg.

Drawn from anchor low to extreme high: divides the vertical leg into thirds, then draws
lines from anchor to each third-point at the time-target. Tests current price against
these speed lines as dynamic supports.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_speed_resistance"
WEIGHT_DEFAULT = 0.55
SPEED_LEVELS = [1 / 3, 2 / 3]


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
    b_i_global = a_i + 1 + b_i_rel
    dp = b_p - a_p
    dt = b_i_global - a_i
    if dt <= 0 or dp <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    cur_t_in_win = len(win) - 1
    bars_since_a = cur_t_in_win - a_i
    speed_prices = {}
    for lv in SPEED_LEVELS:
        slope = lv * dp / dt
        speed_prices[f"speed_{round(lv, 3)}"] = round(a_p + slope * bars_since_a, 5)
    last_c = float(df["c"].iloc[-1])
    nearest_lvl = min(SPEED_LEVELS, key=lambda lv: abs(last_c - speed_prices[f"speed_{round(lv, 3)}"]))
    diff = abs(last_c - speed_prices[f"speed_{round(nearest_lvl, 3)}"])
    on_line = diff < dp * 0.025
    payload = {"anchor": a_p, "high": b_p, "speed_lines": speed_prices,
               "nearest_level": round(nearest_lvl, 3), "on_speed_line": on_line}
    if on_line and last_c > float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if on_line and last_c < float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FibonacciSpeedResistanceAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
