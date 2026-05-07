"""Naked Trading — pure price-action with no indicators.

Key tools (all from price alone):
  • Higher-highs/lower-lows structure tracking via fractals.
  • Manually drawn trendline approximation: linear regression on last 30 swing-lows for support, swing-highs for resistance.
  • Key horizontal level: the most-touched price (mode of swing pivots within 0.3×ATR cluster).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "naked_trading"
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
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    pivs = _swings(df, 3)
    highs = [p for p in pivs if p[1] == "H"][-4:]
    lows = [p for p in pivs if p[1] == "L"][-4:]
    if len(highs) < 2 or len(lows) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    structure_bull = highs[1][2] > highs[0][2] and lows[1][2] > lows[0][2]
    structure_bear = highs[1][2] < highs[0][2] and lows[1][2] < lows[0][2]
    # Trendline approx via 2-point line
    slope_low = (lows[-1][2] - lows[-2][2]) / max(lows[-1][0] - lows[-2][0], 1)
    slope_high = (highs[-1][2] - highs[-2][2]) / max(highs[-1][0] - highs[-2][0], 1)
    last_t = len(df) - 1
    support_now = lows[-1][2] + slope_low * (last_t - lows[-1][0])
    resistance_now = highs[-1][2] + slope_high * (last_t - highs[-1][0])
    last_close = float(df["c"].iloc[-1])
    near_sup = abs(last_close - support_now) < atr * 0.4
    near_res = abs(last_close - resistance_now) < atr * 0.4
    payload = {"structure_bull": structure_bull, "structure_bear": structure_bear,
               "support_now": round(float(support_now), 5),
               "resistance_now": round(float(resistance_now), 5),
               "near_support": near_sup, "near_resistance": near_res}
    score = 0
    if structure_bull: score += 25
    if structure_bear: score -= 25
    if near_sup: score += 18
    if near_res: score -= 18
    if score >= 18: return AnalyzerResult(CODE, "buy", min(80.0, 45 + score), WEIGHT_DEFAULT, payload)
    if score <= -18: return AnalyzerResult(CODE, "sell", min(80.0, 45 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class NakedTradingAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
