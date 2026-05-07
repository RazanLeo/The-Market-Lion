"""Fibonacci Fan — diagonal lines from anchor at fib slopes (38.2/50/61.8 of leg).

Connects anchor (last swing low) to high. From anchor, draws fan lines whose end-points
fall at 38.2% / 50% / 61.8% of the price-leg height at the time-target. Tests whether
current price sits on a fan line (potential dynamic support / resistance).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_fan"
WEIGHT_DEFAULT = 0.55
FAN_LEVELS = [0.382, 0.5, 0.618]


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
    delta_t = b_i_global - a_i
    delta_p = b_p - a_p
    if delta_t <= 0 or delta_p <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    cur_t_in_win = len(win) - 1
    bars_since_a = cur_t_in_win - a_i
    fan_prices = {}
    for lv in FAN_LEVELS:
        target_p = a_p + lv * delta_p
        slope = (target_p - a_p) / delta_t
        fan_prices[f"fan_{lv}"] = round(a_p + slope * bars_since_a, 5)
    last_c = float(df["c"].iloc[-1])
    nearest_lvl = min(FAN_LEVELS, key=lambda lv: abs(last_c - fan_prices[f"fan_{lv}"]))
    diff = abs(last_c - fan_prices[f"fan_{nearest_lvl}"])
    on_fan = diff < delta_p * 0.02
    payload = {"anchor_low": a_p, "high_b": b_p, "fan_lines": fan_prices,
               "nearest_level": nearest_lvl, "on_fan": on_fan,
               "diff_to_fan": round(diff, 5)}
    if on_fan and nearest_lvl >= 0.5 and last_c > float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if on_fan and nearest_lvl <= 0.382 and last_c < float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FibonacciFanAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
