"""Moving Average school — SMA(50)+SMA(200) trend filter, EMA(20)+EMA(50) momentum,
Golden/Death cross detection, MA stacking confluence.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "moving_average_school"
WEIGHT_DEFAULT = 1.05


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 220:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    sma50 = c.rolling(50).mean()
    sma200 = c.rolling(200).mean()
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()

    last_c = float(c.iloc[-1])
    s50 = float(sma50.iloc[-1]); s200 = float(sma200.iloc[-1])
    e20 = float(ema20.iloc[-1]); e50 = float(ema50.iloc[-1])
    s50_prev = float(sma50.iloc[-2]); s200_prev = float(sma200.iloc[-2])

    golden_cross = s50_prev <= s200_prev and s50 > s200
    death_cross = s50_prev >= s200_prev and s50 < s200

    # Stack: bullish = price > e20 > e50 > s50 > s200
    stack_bull = last_c > e20 > e50 > s50 > s200
    stack_bear = last_c < e20 < e50 < s50 < s200

    # Slope
    s50_slope = (s50 - float(sma50.iloc[-10])) / float(sma50.iloc[-10]) if not pd.isna(sma50.iloc[-10]) else 0
    s200_slope = (s200 - float(sma200.iloc[-10])) / float(sma200.iloc[-10]) if not pd.isna(sma200.iloc[-10]) else 0

    # Distance from key MA
    pct_from_s200 = (last_c - s200) / s200 * 100

    payload = {
        "price": round(last_c, 5),
        "sma50": round(s50, 5), "sma200": round(s200, 5),
        "ema20": round(e20, 5), "ema50": round(e50, 5),
        "golden_cross_now": golden_cross, "death_cross_now": death_cross,
        "stack_bull": stack_bull, "stack_bear": stack_bear,
        "sma50_slope_pct": round(s50_slope * 100, 3),
        "sma200_slope_pct": round(s200_slope * 100, 3),
        "distance_from_sma200_pct": round(pct_from_s200, 2),
    }

    score = 0.0
    if golden_cross: score += 40
    if death_cross: score -= 40
    if stack_bull: score += 25
    if stack_bear: score -= 25
    if not stack_bull and not stack_bear:
        # partial alignment
        if last_c > s200: score += 8
        if last_c < s200: score -= 8
        if e20 > e50: score += 5
        if e20 < e50: score -= 5
    if s50_slope > 0.005: score += 6
    if s50_slope < -0.005: score -= 6

    if score >= 25:
        return AnalyzerResult(CODE, "buy", min(90.0, 50 + score * 0.7), WEIGHT_DEFAULT, payload)
    if score <= -25:
        return AnalyzerResult(CODE, "sell", min(90.0, 50 + abs(score) * 0.7), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class MovingAverageSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
