"""Stochastic Oscillator School — %K and %D (slow), zone exits + divergence.

%K = 100 × (C - L14) / (H14 - L14)
%D = SMA(3) of %K
Slow Stochastic = SMA(3) of %K, then SMA(3) of that.
Bull cross in oversold (<20) = buy; bear cross in overbought (>80) = sell.
Bull/bear divergence vs price.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "stochastic_school"
WEIGHT_DEFAULT = 0.9


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    ll = l.rolling(14).min(); hh = h.rolling(14).max()
    k = 100 * (c - ll) / (hh - ll + 1e-9)
    slow_k = k.rolling(3).mean()
    slow_d = slow_k.rolling(3).mean()
    K, D = float(slow_k.iloc[-1]), float(slow_d.iloc[-1])
    Kp, Dp = float(slow_k.iloc[-2]), float(slow_d.iloc[-2])
    cross_up = Kp <= Dp and K > D
    cross_dn = Kp >= Dp and K < D
    zone = "overbought" if K > 80 else "oversold" if K < 20 else "mid"
    # Divergence
    win = df.iloc[-30:]; k_w = slow_k.iloc[-30:]
    p_high = int(win["c"].argmax()); p_low = int(win["c"].argmin())
    bull_div = bear_div = False
    if p_high > 5:
        earlier = int(win["c"].iloc[:p_high].argmax())
        if win["c"].iloc[p_high] > win["c"].iloc[earlier] and k_w.iloc[p_high] < k_w.iloc[earlier]:
            bear_div = True
    if p_low > 5:
        earlier = int(win["c"].iloc[:p_low].argmin())
        if win["c"].iloc[p_low] < win["c"].iloc[earlier] and k_w.iloc[p_low] > k_w.iloc[earlier]:
            bull_div = True
    payload = {"%K": round(K, 1), "%D": round(D, 1), "zone": zone,
               "cross_up": cross_up, "cross_down": cross_dn,
               "bull_div": bull_div, "bear_div": bear_div}
    if bull_div and zone == "oversold": return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if bear_div and zone == "overbought": return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    if cross_up and zone == "oversold": return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if cross_dn and zone == "overbought": return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if cross_up and zone == "mid": return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    if cross_dn and zone == "mid": return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class StochasticSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
