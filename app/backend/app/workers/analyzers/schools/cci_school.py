"""CCI School — Commodity Channel Index + zone + divergence + zero-line cross.

CCI = (TP - SMA20(TP)) / (0.015 × Mean Deviation)
TP = (H + L + C) / 3
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "cci_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    tp = (df["h"] + df["l"] + df["c"]) / 3
    sma_tp = tp.rolling(20).mean()
    mean_dev = (tp - sma_tp).abs().rolling(20).mean()
    cci = (tp - sma_tp) / (0.015 * mean_dev.replace(0, 1e-9))
    last = float(cci.iloc[-1]); prev = float(cci.iloc[-2])
    zone = "extreme_overbought" if last > 200 else "overbought" if last > 100 else \
           "oversold" if last < -100 else "extreme_oversold" if last < -200 else "neutral"
    cross_up_zero = prev <= 0 and last > 0
    cross_dn_zero = prev >= 0 and last < 0
    cross_up_100 = prev <= 100 and last > 100
    cross_dn_neg100 = prev >= -100 and last < -100
    # Divergence
    win = df.iloc[-30:]; cci_w = cci.iloc[-30:]
    p_high = int(win["c"].argmax()); p_low = int(win["c"].argmin())
    bull_div = bear_div = False
    if p_high > 5:
        earlier = int(win["c"].iloc[:p_high].argmax())
        if win["c"].iloc[p_high] > win["c"].iloc[earlier] and cci_w.iloc[p_high] < cci_w.iloc[earlier]:
            bear_div = True
    if p_low > 5:
        earlier = int(win["c"].iloc[:p_low].argmin())
        if win["c"].iloc[p_low] < win["c"].iloc[earlier] and cci_w.iloc[p_low] > cci_w.iloc[earlier]:
            bull_div = True
    payload = {"cci": round(last, 1), "zone": zone, "cross_up_zero": cross_up_zero,
               "cross_down_zero": cross_dn_zero, "cross_up_100": cross_up_100,
               "cross_down_neg100": cross_dn_neg100, "bull_div": bull_div, "bear_div": bear_div}
    if bull_div: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if bear_div: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if cross_up_100: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if cross_dn_neg100: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if zone == "extreme_oversold" and prev < last: return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if zone == "extreme_overbought" and prev > last: return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CciSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
