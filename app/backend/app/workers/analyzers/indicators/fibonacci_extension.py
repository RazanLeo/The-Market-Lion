"""Fibonacci Extension — 1.272 / 1.618 / 2.618 projection levels.

After a 3-leg ABC pullback, projects target prices using the AB leg height. Detects
A=lowest_low, B=highest_high after A, C=current pullback low (must be > A). Targets:
  T1 = C + 1.272 × (B-A)
  T2 = C + 1.618 × (B-A)
  T3 = C + 2.618 × (B-A)
Buy signal when price approaches T1 in an uptrend.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_extension"
WEIGHT_DEFAULT = 0.95
EXT_LEVELS = [1.272, 1.618, 2.618]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-100:]
    a_i = int(win["l"].argmin()); a = float(win["l"].iloc[a_i])
    after_a = win.iloc[a_i + 1:]
    if len(after_a) < 8:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    b_i_rel = int(after_a["h"].argmax())
    b = float(after_a["h"].iloc[b_i_rel])
    after_b = after_a.iloc[b_i_rel + 1:]
    if len(after_b) < 3:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c_i_rel = int(after_b["l"].argmin())
    c = float(after_b["l"].iloc[c_i_rel])
    if not (a < c < b):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    leg = b - a
    targets = {f"T{i+1}_{lv}": round(c + lv * leg, 5) for i, lv in enumerate(EXT_LEVELS)}
    last_c = float(df["c"].iloc[-1])
    nearest_t = min(targets.values(), key=lambda t: abs(last_c - t))
    on_target = abs(last_c - nearest_t) < (b - a) * 0.02
    payload = {"A": round(a, 5), "B": round(b, 5), "C": round(c, 5),
               "targets": targets, "on_target": on_target,
               "nearest_target": round(nearest_t, 5)}
    if last_c > b * 1.001:  # broke B → projecting upward
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if on_target and last_c >= targets[f"T1_{EXT_LEVELS[0]}"]:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)  # take profit zone
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FibonacciExtensionAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
