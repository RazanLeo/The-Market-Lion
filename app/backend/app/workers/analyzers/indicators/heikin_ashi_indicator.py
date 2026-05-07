"""Heikin Ashi candles + persistence. HA_close=(O+H+L+C)/4; HA_open=(prev_HA_open+prev_HA_close)/2."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "heikin_ashi_indicator"; WEIGHT_DEFAULT = 0.8
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ha_close = (df["o"] + df["h"] + df["l"] + df["c"]) / 4
    ha_open = pd.Series(index=df.index, dtype=float)
    ha_open.iloc[0] = (df["o"].iloc[0] + df["c"].iloc[0]) / 2
    for i in range(1, len(df)):
        ha_open.iloc[i] = (ha_open.iloc[i - 1] + ha_close.iloc[i - 1]) / 2
    streak = 1; cur = "up" if ha_close.iloc[-1] > ha_open.iloc[-1] else "down"
    for i in range(2, min(len(df), 20)):
        prev = "up" if ha_close.iloc[-i] > ha_open.iloc[-i] else "down"
        if prev == cur: streak += 1
        else: break
    payload = {"ha_open": round(float(ha_open.iloc[-1]), 5),
               "ha_close": round(float(ha_close.iloc[-1]), 5),
               "streak": streak, "current": cur}
    if streak >= 3 and cur == "up": return AnalyzerResult(CODE, "buy", min(75.0, 45 + streak * 4), WEIGHT_DEFAULT, payload)
    if streak >= 3 and cur == "down": return AnalyzerResult(CODE, "sell", min(75.0, 45 + streak * 4), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class HeikinAshiIndicatorIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
