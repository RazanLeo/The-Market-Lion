"""Kagi Chart School — lines reverse only on close beyond reversal threshold.

Yang line (thick) appears when price closes above the previous shoulder.
Yin line (thin) appears when price closes below the previous waist.
Reversal threshold = 4×ATR(14).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "kagi_chart_school"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 0)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    threshold = 4 * atr
    direction = 0  # +1 yang, -1 yin
    last_extreme = float(df["c"].iloc[0])
    last_shoulder = last_waist = last_extreme
    yangs = yins = 0
    for p in df["c"].iloc[1:]:
        p = float(p)
        if direction in (0, 1):
            if p > last_extreme:
                last_extreme = p
            elif last_extreme - p >= threshold:
                if direction == 1: last_shoulder = last_extreme
                direction = -1; last_extreme = p; yins += 1
        else:
            if p < last_extreme:
                last_extreme = p
            elif p - last_extreme >= threshold:
                last_waist = last_extreme
                direction = 1; last_extreme = p; yangs += 1
    last_close = float(df["c"].iloc[-1])
    breaking_shoulder = direction == 1 and last_close > last_shoulder
    breaking_waist = direction == -1 and last_close < last_waist
    payload = {"direction": "yang" if direction == 1 else "yin" if direction == -1 else "unknown",
               "yangs_count": yangs, "yins_count": yins,
               "last_shoulder": round(last_shoulder, 5),
               "last_waist": round(last_waist, 5),
               "breaking_shoulder": breaking_shoulder, "breaking_waist": breaking_waist}
    if breaking_shoulder: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if breaking_waist: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if direction == 1: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    if direction == -1: return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class KagiChartSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
