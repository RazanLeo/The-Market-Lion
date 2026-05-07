"""Change in State of Delivery (CISD) — ICT shift between bullish and bearish delivery.

Bullish delivery = sequence of HH/HL pivots. Bearish = LL/LH.
CISD bearish: after a stretch of bullish delivery, the first close that breaks below
              the most-recent significant swing low.
CISD bullish: mirror.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "change_in_state_of_delivery"
WEIGHT_DEFAULT = 0.95


def _swings(df: pd.DataFrame, n: int = 3):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 3)
    if len(pivs) < 6:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    # Determine prior delivery state from pivs[-6:-2]
    prior_highs = [p for p in pivs[-6:-2] if p[1] == "H"]
    prior_lows = [p for p in pivs[-6:-2] if p[1] == "L"]
    if len(prior_highs) < 2 or len(prior_lows) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    prior_bullish = prior_highs[1][2] > prior_highs[0][2] and prior_lows[1][2] > prior_lows[0][2]
    prior_bearish = prior_highs[1][2] < prior_highs[0][2] and prior_lows[1][2] < prior_lows[0][2]
    if not (prior_bullish or prior_bearish):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_close = float(df["c"].iloc[-1])
    # Most recent pivot-low / pivot-high (last few)
    last_swing_low = max((p for p in pivs if p[1] == "L"), key=lambda x: x[0])[2]
    last_swing_high = max((p for p in pivs if p[1] == "H"), key=lambda x: x[0])[2]
    cisd_bear = prior_bullish and last_close < last_swing_low
    cisd_bull = prior_bearish and last_close > last_swing_high
    payload = {"prior_state": "bullish_delivery" if prior_bullish else "bearish_delivery",
               "last_swing_low": round(last_swing_low, 5),
               "last_swing_high": round(last_swing_high, 5),
               "CISD_bearish": cisd_bear, "CISD_bullish": cisd_bull}
    if cisd_bear: return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    if cisd_bull: return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class ChangeInStateOfDeliveryAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
