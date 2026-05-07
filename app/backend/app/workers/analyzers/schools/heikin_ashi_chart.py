"""Heikin-Ashi Chart — color streak + body-to-wick ratio.

HA bars filter noise. Strong trend signals:
  • 5+ consecutive same-color HA bars
  • No opposite-side wick (e.g., bullish bars with no lower wick = strong uptrend)
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "heikin_ashi_chart"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o, h, l, c = df["o"].copy(), df["h"].copy(), df["l"].copy(), df["c"].copy()
    ha_c = (o + h + l + c) / 4
    ha_o = pd.Series(index=df.index, dtype=float)
    ha_o.iloc[0] = (float(o.iloc[0]) + float(c.iloc[0])) / 2
    for i in range(1, len(df)):
        ha_o.iloc[i] = (float(ha_o.iloc[i - 1]) + float(ha_c.iloc[i - 1])) / 2
    ha_h = pd.concat([h, ha_o, ha_c], axis=1).max(axis=1)
    ha_l = pd.concat([l, ha_o, ha_c], axis=1).min(axis=1)
    bullish = ha_c > ha_o
    streak = 0
    for v in bullish.iloc[-15:][::-1]:
        if v == bullish.iloc[-1]: streak += 1
        else: break
    last_color_bull = bool(bullish.iloc[-1])
    upper_wick = float(ha_h.iloc[-1] - max(ha_o.iloc[-1], ha_c.iloc[-1]))
    lower_wick = float(min(ha_o.iloc[-1], ha_c.iloc[-1]) - ha_l.iloc[-1])
    body = abs(float(ha_c.iloc[-1]) - float(ha_o.iloc[-1]))
    no_lower = lower_wick < body * 0.1
    no_upper = upper_wick < body * 0.1
    payload = {"streak": int(streak), "last_color": "bull" if last_color_bull else "bear",
               "no_lower_wick": no_lower, "no_upper_wick": no_upper}
    if last_color_bull and streak >= 5 and no_lower:
        return AnalyzerResult(CODE, "buy", min(85, 50 + streak * 5), WEIGHT_DEFAULT, payload)
    if (not last_color_bull) and streak >= 5 and no_upper:
        return AnalyzerResult(CODE, "sell", min(85, 50 + streak * 5), WEIGHT_DEFAULT, payload)
    if streak >= 3:
        return AnalyzerResult(CODE, "buy" if last_color_bull else "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class HeikinAshiChartAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
