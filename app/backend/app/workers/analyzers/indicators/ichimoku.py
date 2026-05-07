"""Ichimoku (9, 26, 52). Cloud + TK cross."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "ichimoku"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    sa = ((tenkan + kijun) / 2).shift(26)
    sb = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    last_c = float(c.iloc[-1])
    a = float(sa.iloc[-1]) if not pd.isna(sa.iloc[-1]) else last_c
    b = float(sb.iloc[-1]) if not pd.isna(sb.iloc[-1]) else last_c
    cloud_top = max(a, b); cloud_bot = min(a, b)
    above = last_c > cloud_top; below = last_c < cloud_bot
    t = float(tenkan.iloc[-1]); k = float(kijun.iloc[-1])
    tp = float(tenkan.iloc[-2]); kp = float(kijun.iloc[-2])
    cross_up = tp <= kp and t > k
    cross_dn = tp >= kp and t < k
    payload = {"tenkan": round(t, 5), "kijun": round(k, 5),
               "senkou_a": round(a, 5), "senkou_b": round(b, 5),
               "cloud_color": "green" if a > b else "red",
               "cross_up": cross_up, "cross_down": cross_dn}
    if above and t > k: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if below and t < k: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if cross_up: return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if cross_dn: return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class IchimokuIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
