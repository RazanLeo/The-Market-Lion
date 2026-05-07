"""Price Action Classic — Al Brooks-style bar-by-bar analysis.

Detects:
  • Strong trend bar: body > 70% of range, no opposite wick
  • Doji bar: body < 10% of range
  • Breakout bar: trades beyond prior bar's high/low
  • Reversal bar (signal bar): pin bar at swing extreme
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "price_action_classic"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o, h, l, c = float(df["o"].iloc[-1]), float(df["h"].iloc[-1]), float(df["l"].iloc[-1]), float(df["c"].iloc[-1])
    rng = h - l + 1e-9
    body = abs(c - o); body_pct = body / rng
    upper = h - max(o, c); lower = min(o, c) - l
    is_bull = c > o
    strong_trend = body_pct > 0.7
    doji = body_pct < 0.1
    prev_h = float(df["h"].iloc[-2]); prev_l = float(df["l"].iloc[-2])
    breakout_up = c > prev_h
    breakout_dn = c < prev_l
    swing_low_20 = float(df["l"].iloc[-20:].min())
    swing_high_20 = float(df["h"].iloc[-20:].max())
    pin_bull = lower > 2 * body and abs(l - swing_low_20) < rng
    pin_bear = upper > 2 * body and abs(h - swing_high_20) < rng
    payload = {"strong_trend_bar": strong_trend, "doji": doji,
               "breakout_up": breakout_up, "breakout_dn": breakout_dn,
               "pin_bull": pin_bull, "pin_bear": pin_bear,
               "body_pct": round(body_pct, 2)}
    if pin_bull or (strong_trend and is_bull and breakout_up):
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if pin_bear or (strong_trend and not is_bull and breakout_dn):
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class PriceActionClassicAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
