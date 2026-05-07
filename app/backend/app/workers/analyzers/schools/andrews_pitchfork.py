"""Andrews Pitchfork — Median line and parallel channels from 3 pivots P0, P1, P2."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "andrews_pitchfork"
WEIGHT_DEFAULT = 0.95


def _swings(df: pd.DataFrame, n: int = 5):
    highs, lows = [], []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max(): highs.append(i)
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min(): lows.append(i)
    return highs, lows


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    highs, lows = _swings(df, 5)
    pivots = sorted([(i, "H", float(df["h"].iloc[i])) for i in highs] +
                    [(i, "L", float(df["l"].iloc[i])) for i in lows])
    if len(pivots) < 3:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last3 = pivots[-3:]
    P0, P1, P2 = last3
    types = "".join(p[1] for p in last3)
    if types not in ("LHL", "HLH", "LLH", "HHL"):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})
    t0, _, p0 = P0; t1, _, p1 = P1; t2, _, p2 = P2
    m_t = (t1 + t2) / 2.0; m_p = (p1 + p2) / 2.0
    if m_t - t0 == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    slope = (m_p - p0) / (m_t - t0)
    last_t = len(df) - 1
    ml_now = p0 + slope * (last_t - t0)
    upper_now = p1 + slope * (last_t - t1)
    lower_now = p2 + slope * (last_t - t2)
    if upper_now < lower_now:
        upper_now, lower_now = lower_now, upper_now
    last_close = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    near_upper = abs(last_close - upper_now) < atr * 0.4
    near_lower = abs(last_close - lower_now) < atr * 0.4
    near_ml = abs(last_close - ml_now) < atr * 0.3
    above_ml = last_close > ml_now

    payload = {"P0": (int(t0), round(p0, 5)), "P1": (int(t1), round(p1, 5)), "P2": (int(t2), round(p2, 5)),
               "slope_per_bar": round(float(slope), 6),
               "median_line_now": round(float(ml_now), 5),
               "upper_parallel_now": round(float(upper_now), 5),
               "lower_parallel_now": round(float(lower_now), 5),
               "near_upper": near_upper, "near_lower": near_lower, "near_ml": near_ml,
               "trend_via_slope": "up" if slope > 0 else "down"}
    score = 0.0
    if near_lower: score += 28
    if near_upper: score -= 28
    if near_ml: score += 15 if slope > 0 else -15
    if above_ml and slope > 0: score += 8
    if not above_ml and slope < 0: score -= 8

    if score >= 18:
        return AnalyzerResult(CODE, "buy", min(80.0, 45 + score), WEIGHT_DEFAULT, payload)
    if score <= -18:
        return AnalyzerResult(CODE, "sell", min(80.0, 45 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class AndrewsPitchforkAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
