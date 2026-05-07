"""Megaphone Pattern (5-point reversal) — 3 lower lows alternating with 2 higher highs at top, mirror at bottom.

A megaphone is essentially a broadening formation acting as a reversal:
  Top:   H1 → L1 → H2(>H1) → L2(<L1) → H3(>H2)  ⇒ expect bearish reversal at H3.
  Bottom: L1 → H1 → L2(<L1) → H2(>H1) → L3(<L2) ⇒ expect bullish reversal at L3.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "megaphone_pattern"
WEIGHT_DEFAULT = 0.85


def _swings(df: pd.DataFrame, n: int = 4):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 4)
    if len(pivs) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last5 = pivs[-5:]
    types = "".join(p[1] for p in last5)
    P = [p[2] for p in last5]
    is_top = is_bottom = False
    if types == "HLHLH":
        if P[2] > P[0] and P[3] < P[1] and P[4] > P[2]:
            is_top = True
    if types == "LHLHL":
        if P[2] < P[0] and P[3] > P[1] and P[4] < P[2]:
            is_bottom = True

    if not (is_top or is_bottom):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})

    last_close = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    near_terminal = abs(last_close - P[4]) < atr * 0.6

    payload = {"types": types, "terminal_pivot": round(P[4], 5),
               "near_terminal": near_terminal,
               "setup": "megaphone_top" if is_top else "megaphone_bottom"}
    if not near_terminal:
        return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)
    if is_top:
        return AnalyzerResult(CODE, "sell", 75.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "buy", 75.0, WEIGHT_DEFAULT, payload)


class MegaphonePatternAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
