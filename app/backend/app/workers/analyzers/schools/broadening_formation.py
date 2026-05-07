"""Broadening Formation (Expanding Triangle) — successively higher-highs and lower-lows over 5 pivots.

Bearish (top): trade short at upper trendline test.
Bullish (bottom): trade long at lower trendline test.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "broadening_formation"
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
    highs = [p for p in last5 if p[1] == "H"]
    lows = [p for p in last5 if p[1] == "L"]
    if len(highs) < 2 or len(lows) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    higher_highs = all(highs[i + 1][2] > highs[i][2] for i in range(len(highs) - 1))
    lower_lows = all(lows[i + 1][2] < lows[i][2] for i in range(len(lows) - 1))
    if not (higher_highs and lower_lows):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT,
                              {"hh": higher_highs, "ll": lower_lows})

    # Project upper / lower trendlines to current bar
    if len(highs) >= 2:
        h1, h2 = highs[-2], highs[-1]
        slope_up = (h2[2] - h1[2]) / (h2[0] - h1[0]) if h2[0] - h1[0] else 0
        upper_now = h2[2] + slope_up * (len(df) - 1 - h2[0])
    else:
        upper_now = highs[-1][2]
    if len(lows) >= 2:
        l1, l2 = lows[-2], lows[-1]
        slope_dn = (l2[2] - l1[2]) / (l2[0] - l1[0]) if l2[0] - l1[0] else 0
        lower_now = l2[2] + slope_dn * (len(df) - 1 - l2[0])
    else:
        lower_now = lows[-1][2]

    last_close = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    near_upper = abs(last_close - upper_now) < atr * 0.5
    near_lower = abs(last_close - lower_now) < atr * 0.5

    payload = {
        "upper_trendline": round(float(upper_now), 5),
        "lower_trendline": round(float(lower_now), 5),
        "near_upper": near_upper, "near_lower": near_lower,
    }
    if near_upper:
        return AnalyzerResult(CODE, "sell", 70.0, WEIGHT_DEFAULT, payload)
    if near_lower:
        return AnalyzerResult(CODE, "buy", 70.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)


class BroadeningFormationAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
