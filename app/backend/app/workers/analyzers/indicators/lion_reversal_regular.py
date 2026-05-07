"""Lion Regular Reversal — single-bar reversal at swing extreme.

Detects:
  - Bullish pin bar at swing low: lower wick > 2× body, body in upper third
  - Bearish pin bar at swing high: upper wick > 2× body, body in lower third
  - Bullish engulfing at swing low: green bar fully engulfs prior red
  - Bearish engulfing at swing high: red bar fully engulfs prior green
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_reversal_regular"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o0 = float(df["o"].iloc[-2]); c0 = float(df["c"].iloc[-2])
    o1 = float(df["o"].iloc[-1]); c1 = float(df["c"].iloc[-1])
    h1 = float(df["h"].iloc[-1]); l1 = float(df["l"].iloc[-1])
    body1 = abs(c1 - o1); rng1 = h1 - l1 + 1e-9
    upper_wick = h1 - max(o1, c1); lower_wick = min(o1, c1) - l1
    swing_low_20 = float(df["l"].iloc[-20:].min())
    swing_high_20 = float(df["h"].iloc[-20:].max())
    near_low = abs(l1 - swing_low_20) < rng1 * 0.5
    near_high = abs(h1 - swing_high_20) < rng1 * 0.5
    bull_pin = lower_wick > 2 * body1 and (max(o1, c1) - l1) / rng1 > 0.66 and near_low
    bear_pin = upper_wick > 2 * body1 and (h1 - min(o1, c1)) / rng1 > 0.66 and near_high
    bull_engulf = c1 > o0 and o1 < c0 and c0 < o0 and near_low
    bear_engulf = c1 < o0 and o1 > c0 and c0 > o0 and near_high
    payload = {"bull_pin": bull_pin, "bear_pin": bear_pin,
               "bull_engulf": bull_engulf, "bear_engulf": bear_engulf,
               "near_swing_low": near_low, "near_swing_high": near_high}
    if bull_pin or bull_engulf:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if bear_pin or bear_engulf:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionReversalRegularAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
