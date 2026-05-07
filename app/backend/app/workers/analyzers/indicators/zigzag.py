"""ZigZag — peaks/troughs filter with min %swing = 1.5%. Most recent ZZ direction = bias."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "zigzag"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    th = 0.015
    pivots = [(0, float(df["c"].iloc[0]))]
    direction = 0; last_idx, last_p = 0, float(df["c"].iloc[0])
    for i in range(1, len(df)):
        p = float(df["c"].iloc[i])
        if direction >= 0 and p > last_p: last_idx, last_p = i, p
        elif direction <= 0 and p < last_p: last_idx, last_p = i, p
        if direction in (0, 1) and (last_p - p) / last_p >= th:
            pivots.append((last_idx, last_p)); direction = -1; last_idx, last_p = i, p
        elif direction in (0, -1) and (p - last_p) / last_p >= th:
            pivots.append((last_idx, last_p)); direction = 1; last_idx, last_p = i, p
    pivots.append((last_idx, last_p))
    if len(pivots) < 3: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    payload = {"last_pivot_price": round(pivots[-1][1], 5), "pivots_count": len(pivots),
               "current_direction": "up" if direction == 1 else "down" if direction == -1 else "unknown"}
    if direction == 1: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if direction == -1: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class ZigzagIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
