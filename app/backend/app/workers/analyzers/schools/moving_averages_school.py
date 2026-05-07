"""Moving Averages School — golden/death cross + multi-MA stack alignment.

Detects:
  • Golden Cross: SMA50 crosses above SMA200
  • Death Cross: SMA50 crosses below SMA200
  • Stack alignment: EMA10 > EMA20 > SMA50 > SMA200 (perfect bull)
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "moving_averages_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 220:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    ema10 = c.ewm(span=10, adjust=False).mean()
    ema20 = c.ewm(span=20, adjust=False).mean()
    sma50 = c.rolling(50).mean()
    sma200 = c.rolling(200).mean()
    golden = (sma50.iloc[-2] <= sma200.iloc[-2]) and (sma50.iloc[-1] > sma200.iloc[-1])
    death = (sma50.iloc[-2] >= sma200.iloc[-2]) and (sma50.iloc[-1] < sma200.iloc[-1])
    perfect_bull = (float(ema10.iloc[-1]) > float(ema20.iloc[-1]) > float(sma50.iloc[-1]) > float(sma200.iloc[-1]))
    perfect_bear = (float(ema10.iloc[-1]) < float(ema20.iloc[-1]) < float(sma50.iloc[-1]) < float(sma200.iloc[-1]))
    payload = {"golden_cross": bool(golden), "death_cross": bool(death),
               "perfect_bull_stack": perfect_bull, "perfect_bear_stack": perfect_bear}
    if golden:
        return AnalyzerResult(CODE, "buy", 85, WEIGHT_DEFAULT, payload)
    if death:
        return AnalyzerResult(CODE, "sell", 85, WEIGHT_DEFAULT, payload)
    if perfect_bull:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if perfect_bear:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MovingAveragesSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
