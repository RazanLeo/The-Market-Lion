"""Seasonality — day-of-week and hour-of-day bias.

Computes average return for current day-of-week and hour-of-day across history.
Bullish bias if both are positive; bearish if both negative.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "seasonality"
WEIGHT_DEFAULT = 0.5


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rets = df["c"].pct_change().fillna(0)
    df2 = pd.DataFrame({"r": rets, "dow": df.index.dayofweek, "hour": df.index.hour})
    dow_now = df.index[-1].dayofweek
    hour_now = df.index[-1].hour
    dow_mean = float(df2[df2["dow"] == dow_now]["r"].mean())
    hour_mean = float(df2[df2["hour"] == hour_now]["r"].mean())
    payload = {"dow_now": int(dow_now), "hour_now": int(hour_now),
               "dow_avg_return": round(dow_mean, 6),
               "hour_avg_return": round(hour_mean, 6)}
    if dow_mean > 0 and hour_mean > 0:
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if dow_mean < 0 and hour_mean < 0:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SeasonalityAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
