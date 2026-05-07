"""Ichimoku Cloud (full) — all 5 lines + Chikou cross signal.

  Tenkan-sen (9): (max(h,9) + min(l,9)) / 2
  Kijun-sen (26): (max(h,26) + min(l,26)) / 2
  Senkou A : (Tenkan + Kijun) / 2 shifted +26
  Senkou B : (max(h,52) + min(l,52)) / 2 shifted +26
  Chikou : close shifted -26
Buy: close above cloud + Tenkan > Kijun + Chikou above price 26 bars ago.
Sell: mirror.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "ichimoku_cloud_full"
WEIGHT_DEFAULT = 1.1


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    span_a = ((tenkan + kijun) / 2).shift(26)
    span_b = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    chikou = c.shift(-26)
    last_c = float(c.iloc[-1])
    last_t = float(tenkan.iloc[-1] or 0); last_k = float(kijun.iloc[-1] or 0)
    last_a = float(span_a.iloc[-1] or 0); last_b = float(span_b.iloc[-1] or 0)
    cloud_top = max(last_a, last_b); cloud_bot = min(last_a, last_b)
    above_cloud = last_c > cloud_top
    below_cloud = last_c < cloud_bot
    in_cloud = cloud_bot <= last_c <= cloud_top
    tk_cross_up = last_t > last_k
    if len(c) > 27:
        chikou_above_price = float(c.iloc[-1]) > float(c.iloc[-27])
    else:
        chikou_above_price = False
    cloud_color_bull = last_a > last_b  # green cloud
    payload = {"tenkan": round(last_t, 5), "kijun": round(last_k, 5),
               "span_a": round(last_a, 5), "span_b": round(last_b, 5),
               "above_cloud": above_cloud, "below_cloud": below_cloud, "in_cloud": in_cloud,
               "tk_cross": "bull" if tk_cross_up else "bear",
               "chikou_signal": "bull" if chikou_above_price else "bear",
               "cloud_color": "green" if cloud_color_bull else "red"}
    score = 0
    if above_cloud: score += 30
    if below_cloud: score -= 30
    if tk_cross_up: score += 20
    else: score -= 20
    if chikou_above_price: score += 20
    else: score -= 20
    if cloud_color_bull: score += 10
    else: score -= 10
    if score >= 50:
        return AnalyzerResult(CODE, "buy", min(90, 40 + score), WEIGHT_DEFAULT, payload)
    if score <= -50:
        return AnalyzerResult(CODE, "sell", min(90, 40 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class IchimokuCloudFullAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
