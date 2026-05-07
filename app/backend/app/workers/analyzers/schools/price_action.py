"""Price Action — Pin Bar / Engulfing / Inside / Outside / Fakey detection on the latest 1-3 bars.

Strict definitions used:
  Pin Bar (bullish): body ≤ 30% of range, lower shadow ≥ 60%, upper shadow ≤ 25%, closes in upper half.
  Pin Bar (bearish): mirror image.
  Bullish Engulfing: prev candle red, current green, current body engulfs prev body (open ≤ prev close, close ≥ prev open).
  Bearish Engulfing: mirror.
  Inside Bar: current high ≤ prev high AND current low ≥ prev low.
  Outside Bar: current high > prev high AND current low < prev low.
  Fakey: an Inside Bar break that immediately reverses (pierce-then-fail).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "price_action"
WEIGHT_DEFAULT = 1.05


def _bar(df: pd.DataFrame, i: int):
    return float(df["o"].iloc[i]), float(df["h"].iloc[i]), float(df["l"].iloc[i]), float(df["c"].iloc[i])


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o, h, l, c = _bar(df, -1)
    po, ph, pl, pc = _bar(df, -2)
    rng = h - l; body = abs(c - o)
    upper = h - max(c, o); lower = min(c, o) - l
    if rng <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    body_pct = body / rng
    up_pct = upper / rng; lo_pct = lower / rng

    pin_bull = body_pct <= 0.30 and lo_pct >= 0.60 and up_pct <= 0.25 and c > (h + l) / 2
    pin_bear = body_pct <= 0.30 and up_pct >= 0.60 and lo_pct <= 0.25 and c < (h + l) / 2

    eng_bull = pc < po and c > o and o <= pc and c >= po
    eng_bear = pc > po and c < o and o >= pc and c <= po

    inside = h <= ph and l >= pl
    outside = h > ph and l < pl

    # Fakey: prev was inside bar of pre-prev (at index -3); current pierces & closes back inside
    fakey_bull = fakey_bear = False
    if len(df) >= 4:
        pp_o, pp_h, pp_l, pp_c = _bar(df, -3)
        prev_inside = ph <= pp_h and pl >= pp_l
        if prev_inside:
            fakey_bull = l < pl and c > pl
            fakey_bear = h > ph and c < ph

    payload = {
        "body_pct": round(body_pct, 3), "upper_pct": round(up_pct, 3), "lower_pct": round(lo_pct, 3),
        "pin_bull": pin_bull, "pin_bear": pin_bear,
        "eng_bull": eng_bull, "eng_bear": eng_bear,
        "inside_bar": inside, "outside_bar": outside,
        "fakey_bull": fakey_bull, "fakey_bear": fakey_bear,
    }

    score = 0.0
    if pin_bull: score += 35
    if pin_bear: score -= 35
    if eng_bull: score += 30
    if eng_bear: score -= 30
    if fakey_bull: score += 28
    if fakey_bear: score -= 28
    if outside and c > o: score += 12
    if outside and c < o: score -= 12
    if inside:
        # follow trend on inside bar consolidation
        trend = 1 if df["c"].iloc[-1] > df["c"].iloc[-10] else -1
        score += trend * 6

    if score >= 20:
        return AnalyzerResult(CODE, "buy", min(85.0, 40 + score), WEIGHT_DEFAULT, payload)
    if score <= -20:
        return AnalyzerResult(CODE, "sell", min(85.0, 40 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class PriceActionAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
