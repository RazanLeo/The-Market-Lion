"""Ichimoku School — Kumo (cloud) thickness ratio + Kumo break detection.

Distinct from full ichimoku indicator: focuses on cloud-twist (Senkou A vs Senkou B
crossover) and Kumo-break breakout signals. Cloud thickness as % of price = volatility
proxy.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "ichimoku_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    span_a = ((tenkan + kijun) / 2).shift(26)
    span_b = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    last_a = float(span_a.iloc[-1] or 0)
    last_b = float(span_b.iloc[-1] or 0)
    last_c = float(c.iloc[-1])
    kumo_top = max(last_a, last_b); kumo_bot = min(last_a, last_b)
    thickness = (kumo_top - kumo_bot) / last_c if last_c > 0 else 0
    # Twist = a/b crossover within last 5 bars
    twist_up = any(span_a.iloc[i] <= span_b.iloc[i] and span_a.iloc[i + 1] > span_b.iloc[i + 1]
                    for i in range(len(span_a) - 6, len(span_a) - 1)
                    if not pd.isna(span_a.iloc[i]) and not pd.isna(span_b.iloc[i]))
    twist_dn = any(span_a.iloc[i] >= span_b.iloc[i] and span_a.iloc[i + 1] < span_b.iloc[i + 1]
                    for i in range(len(span_a) - 6, len(span_a) - 1)
                    if not pd.isna(span_a.iloc[i]) and not pd.isna(span_b.iloc[i]))
    # Kumo break: was inside cloud last bar, now above/below
    prev_top = max(float(span_a.iloc[-2] or 0), float(span_b.iloc[-2] or 0))
    prev_bot = min(float(span_a.iloc[-2] or 0), float(span_b.iloc[-2] or 0))
    prev_c = float(c.iloc[-2])
    kumo_break_up = prev_bot <= prev_c <= prev_top and last_c > kumo_top
    kumo_break_dn = prev_bot <= prev_c <= prev_top and last_c < kumo_bot
    payload = {"thickness_pct_price": round(thickness * 100, 3),
               "kumo_top": round(kumo_top, 5), "kumo_bot": round(kumo_bot, 5),
               "twist_up": twist_up, "twist_dn": twist_dn,
               "kumo_break_up": kumo_break_up, "kumo_break_dn": kumo_break_dn}
    if kumo_break_up:
        return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if kumo_break_dn:
        return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    if twist_up and last_c > kumo_top:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if twist_dn and last_c < kumo_bot:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class IchimokuSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
