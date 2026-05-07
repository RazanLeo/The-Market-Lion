"""Ichimoku Kinko Hyo — full system.

Components (default 9/26/52):
  • Tenkan-sen   = (highest_9 + lowest_9) / 2
  • Kijun-sen    = (highest_26 + lowest_26) / 2
  • Senkou A     = (Tenkan + Kijun) / 2     shifted +26 forward
  • Senkou B     = (highest_52 + lowest_52) / 2  shifted +26 forward
  • Chikou Span  = close shifted -26

Signals:
  • Cloud color: green if SenA > SenB, red if SenB > SenA.
  • Price vs cloud: above (bullish bias), inside (consolidation), below (bearish bias).
  • TK cross: Tenkan crossing Kijun above (bullish) / below (bearish).
  • Kumo twist: Senkou A and B crossing → potential trend change.
  • Chikou clear of price 26 bars ago → momentum confirmation.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "ichimoku"
WEIGHT_DEFAULT = 1.15


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    h, l, c = df["h"], df["l"], df["c"]
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun  = (h.rolling(26).max() + l.rolling(26).min()) / 2
    senA   = ((tenkan + kijun) / 2).shift(26)
    senB   = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    chikou = c.shift(-26)

    last_c = float(c.iloc[-1])
    last_t = float(tenkan.iloc[-1]); last_k = float(kijun.iloc[-1])
    last_a = float(senA.iloc[-1])    if not pd.isna(senA.iloc[-1])   else last_c
    last_b = float(senB.iloc[-1])    if not pd.isna(senB.iloc[-1])   else last_c
    cloud_top = max(last_a, last_b); cloud_bot = min(last_a, last_b)

    cloud_color = "green" if last_a > last_b else "red"
    price_pos = "above" if last_c > cloud_top else "below" if last_c < cloud_bot else "inside"

    # TK cross detection (last 3 bars)
    tk_diff = (tenkan - kijun).fillna(0)
    tk_cross_up = tk_diff.iloc[-2] <= 0 and tk_diff.iloc[-1] > 0
    tk_cross_dn = tk_diff.iloc[-2] >= 0 and tk_diff.iloc[-1] < 0

    # Kumo twist (forward cloud change)
    fwd_a = senA.iloc[-1] if not pd.isna(senA.iloc[-1]) else 0
    fwd_b = senB.iloc[-1] if not pd.isna(senB.iloc[-1]) else 0
    twist_now = (senA.iloc[-2] > senB.iloc[-2] and fwd_a < fwd_b) or \
                (senA.iloc[-2] < senB.iloc[-2] and fwd_a > fwd_b)

    # Chikou clear: 26 bars ago, where was price?
    if len(c) > 26:
        chikou_ref = float(c.iloc[-1])
        price_26_ago = float(c.iloc[-27])
        chikou_clear_up = chikou_ref > price_26_ago
        chikou_clear_dn = chikou_ref < price_26_ago
    else:
        chikou_clear_up = chikou_clear_dn = False

    payload = {
        "tenkan": round(last_t, 5), "kijun": round(last_k, 5),
        "senkou_a": round(last_a, 5), "senkou_b": round(last_b, 5),
        "cloud_color": cloud_color, "price_pos": price_pos,
        "tk_cross_up": bool(tk_cross_up), "tk_cross_down": bool(tk_cross_dn),
        "kumo_twist": bool(twist_now),
        "chikou_clear_up": chikou_clear_up, "chikou_clear_down": chikou_clear_dn,
    }

    score = 0.0
    if price_pos == "above": score += 25
    if price_pos == "below": score -= 25
    if cloud_color == "green": score += 8
    if cloud_color == "red":   score -= 8
    if tk_cross_up:   score += 22
    if tk_cross_dn:   score -= 22
    if twist_now:
        score += -10 if cloud_color == "green" else 10  # twist warns of change
    if chikou_clear_up: score += 8
    if chikou_clear_dn: score -= 8

    if score >= 25:
        return AnalyzerResult(CODE, "buy", min(90.0, 50 + score * 0.7), WEIGHT_DEFAULT, payload)
    if score <= -25:
        return AnalyzerResult(CODE, "sell", min(90.0, 50 + abs(score) * 0.7), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class IchimokuAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
