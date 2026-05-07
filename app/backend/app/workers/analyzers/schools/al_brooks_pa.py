"""Al Brooks bar-by-bar price action — H1/H2 (high-1/high-2) and L1/L2 patterns + signal-bar quality.

Definitions:
  H1 = first bar after a pullback that has a high higher than the previous bar's high (in an uptrend).
  L1 = mirror in downtrend.
  H2 / L2 = second such bar (if H1 fails to follow through, the H2 is often a stronger setup).
  Signal bar = a strong-bodied trend bar in the direction of the trend, with EMA20 nearby.
  Doji bar = open and close near each other (≤ 25% body of range).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "al_brooks_pa"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]; h = df["h"]; l = df["l"]; o = df["o"]
    ema20 = c.ewm(span=20, adjust=False).mean()
    last = float(c.iloc[-1]); last_o = float(o.iloc[-1])
    rng = float(h.iloc[-1] - l.iloc[-1]) or 1e-9
    body_pct = abs(last - last_o) / rng
    trend_bar_bull = body_pct > 0.6 and last > last_o
    trend_bar_bear = body_pct > 0.6 and last < last_o
    doji = body_pct < 0.25

    e20_now = float(ema20.iloc[-1]); e20_prev = float(ema20.iloc[-10])
    trend_up = e20_now > e20_prev * 1.001
    trend_dn = e20_now < e20_prev * 0.999

    # H1 / L1 detection in last 5 bars
    h1 = h2 = l1 = l2 = False
    high_breaks = 0
    low_breaks = 0
    for i in range(-5, 0):
        if i + 1 == 0:
            break
        if h.iloc[i] > h.iloc[i - 1]:
            high_breaks += 1
            if high_breaks == 1: h1 = True
            if high_breaks == 2: h2 = True
        if l.iloc[i] < l.iloc[i - 1]:
            low_breaks += 1
            if low_breaks == 1: l1 = True
            if low_breaks == 2: l2 = True

    near_ema20 = abs(last - e20_now) < (h.iloc[-1] - l.iloc[-1])

    payload = {"trend_up_via_ema20": trend_up, "trend_dn_via_ema20": trend_dn,
               "trend_bar_bull": trend_bar_bull, "trend_bar_bear": trend_bar_bear,
               "doji": doji, "H1": h1, "H2": h2, "L1": l1, "L2": l2,
               "near_ema20": near_ema20}

    score = 0.0
    if trend_up and h2 and trend_bar_bull and near_ema20: score += 50
    elif trend_up and h1 and trend_bar_bull: score += 30
    if trend_dn and l2 and trend_bar_bear and near_ema20: score -= 50
    elif trend_dn and l1 and trend_bar_bear: score -= 30
    if doji and trend_up: score -= 10  # doji in trend = pause
    if doji and trend_dn: score += 10

    if score >= 25: return AnalyzerResult(CODE, "buy", min(85.0, 45 + score), WEIGHT_DEFAULT, payload)
    if score <= -25: return AnalyzerResult(CODE, "sell", min(85.0, 45 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class AlBrooksPaAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
