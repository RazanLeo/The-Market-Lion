"""Trend lines + parallel channels — connect last 2 swing lows / 2 swing highs.

Compute slope, project to current bar, parallel-channel via opposite swing.
Detect price test of trendline (within 0.4×ATR).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "trend_lines_channels"
WEIGHT_DEFAULT = 0.95


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
    highs = [p for p in pivs if p[1] == "H"][-3:]
    lows = [p for p in pivs if p[1] == "L"][-3:]
    if len(highs) < 2 or len(lows) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_t = len(df) - 1; last_close = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    h1, h2 = highs[-2], highs[-1]
    l1, l2 = lows[-2], lows[-1]
    res_slope = (h2[2] - h1[2]) / max(h2[0] - h1[0], 1)
    sup_slope = (l2[2] - l1[2]) / max(l2[0] - l1[0], 1)
    res_now = h2[2] + res_slope * (last_t - h2[0])
    sup_now = l2[2] + sup_slope * (last_t - l2[0])
    # Channel parallel: take support slope through h2 (parallel-up channel) or vice versa
    chan_high = l2[2] + res_slope * (last_t - l2[0])
    chan_low = h2[2] + sup_slope * (last_t - h2[0])
    test_res = abs(last_close - res_now) < atr * 0.4
    test_sup = abs(last_close - sup_now) < atr * 0.4
    broke_res = last_close > res_now * 1.001
    broke_sup = last_close < sup_now * 0.999
    payload = {"resistance_slope": round(float(res_slope), 6),
               "support_slope": round(float(sup_slope), 6),
               "resistance_now": round(float(res_now), 5),
               "support_now": round(float(sup_now), 5),
               "channel_high": round(float(chan_high), 5),
               "channel_low": round(float(chan_low), 5),
               "test_resistance": test_res, "test_support": test_sup,
               "broke_resistance": broke_res, "broke_support": broke_sup}
    if broke_res: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if broke_sup: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if test_sup: return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if test_res: return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class TrendLinesChannelsAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
