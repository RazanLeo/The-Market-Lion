"""ATR(14) Volatility School — regime classification + Chandelier Exit + ATR-expansion detection.

Regimes (vs last 100 bars of ATR):
  • low: ATR ≤ 25th percentile
  • normal: 25-75
  • high: ≥ 75th percentile
Chandelier Exit: longs = highest_high(22) - 3×ATR(22); shorts = lowest_low(22) + 3×ATR(22).
Volatility expansion: ATR(14) rising 30% over last 10 bars → breakout-friendly regime.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "atr_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    atr22 = tr.rolling(22).mean()
    last_atr = float(atr14.iloc[-1])
    last100 = atr14.iloc[-100:].dropna()
    if len(last100) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    p25 = float(np.percentile(last100, 25))
    p75 = float(np.percentile(last100, 75))
    if last_atr <= p25: regime = "low"
    elif last_atr >= p75: regime = "high"
    else: regime = "normal"
    atr_change = (last_atr - float(atr14.iloc[-11])) / float(atr14.iloc[-11]) if not pd.isna(atr14.iloc[-11]) else 0
    expansion = atr_change > 0.3
    contraction = atr_change < -0.3
    hh22 = float(h.rolling(22).max().iloc[-1])
    ll22 = float(l.rolling(22).min().iloc[-1])
    chand_long = hh22 - 3 * float(atr22.iloc[-1])
    chand_short = ll22 + 3 * float(atr22.iloc[-1])
    last_close = float(c.iloc[-1])
    payload = {"atr14": round(last_atr, 5), "regime": regime,
               "atr_change_10bars_pct": round(atr_change * 100, 2),
               "expansion": expansion, "contraction": contraction,
               "chandelier_long_stop": round(chand_long, 5),
               "chandelier_short_stop": round(chand_short, 5)}
    # Direction inferred from EMA slope; ATR doesn't dictate direction directly
    ema20 = c.ewm(span=20, adjust=False).mean()
    direction_up = float(ema20.iloc[-1]) > float(ema20.iloc[-10])
    if expansion and direction_up:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if expansion and not direction_up:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if regime == "low" and last_close < chand_long * 1.001:
        return AnalyzerResult(CODE, "buy", 35, WEIGHT_DEFAULT, payload)  # squeeze before move
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AtrSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
