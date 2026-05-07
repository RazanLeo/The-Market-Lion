"""MACD School — MACD(12,26,9) cross + histogram analysis + divergence + zero-line cross."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "macd_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    last_macd = float(macd.iloc[-1]); last_sig = float(signal.iloc[-1]); last_hist = float(hist.iloc[-1])
    prev_macd = float(macd.iloc[-2]); prev_sig = float(signal.iloc[-2])
    cross_up = prev_macd <= prev_sig and last_macd > last_sig
    cross_dn = prev_macd >= prev_sig and last_macd < last_sig
    above_zero = last_macd > 0
    zero_cross_up = float(macd.iloc[-2]) <= 0 and last_macd > 0
    zero_cross_dn = float(macd.iloc[-2]) >= 0 and last_macd < 0
    hist_trend = "expanding" if abs(last_hist) > abs(float(hist.iloc[-3])) else "contracting"

    win = df.iloc[-30:]; macd_win = macd.iloc[-30:]
    p_high_idx = int(win["c"].argmax()); p_low_idx = int(win["c"].argmin())
    bear_div = bull_div = False
    if p_high_idx > 5 and p_high_idx < 28:
        earlier = int(win["c"].iloc[:p_high_idx].argmax())
        if win["c"].iloc[p_high_idx] > win["c"].iloc[earlier] and macd_win.iloc[p_high_idx] < macd_win.iloc[earlier]:
            bear_div = True
    if p_low_idx > 5 and p_low_idx < 28:
        earlier = int(win["c"].iloc[:p_low_idx].argmin())
        if win["c"].iloc[p_low_idx] < win["c"].iloc[earlier] and macd_win.iloc[p_low_idx] > macd_win.iloc[earlier]:
            bull_div = True

    payload = {"macd": round(last_macd, 5), "signal": round(last_sig, 5),
               "histogram": round(last_hist, 5),
               "cross_up": cross_up, "cross_down": cross_dn,
               "above_zero": above_zero, "zero_cross_up": zero_cross_up, "zero_cross_down": zero_cross_dn,
               "hist_trend": hist_trend, "bull_div": bull_div, "bear_div": bear_div}
    score = 0.0
    if cross_up and above_zero: score += 35
    elif cross_up: score += 22
    if cross_dn and not above_zero: score -= 35
    elif cross_dn: score -= 22
    if zero_cross_up: score += 18
    if zero_cross_dn: score -= 18
    if bull_div: score += 28
    if bear_div: score -= 28
    if hist_trend == "expanding":
        if last_hist > 0: score += 6
        else: score -= 6

    if score >= 22:
        return AnalyzerResult(CODE, "buy", min(90.0, 50 + score), WEIGHT_DEFAULT, payload)
    if score <= -22:
        return AnalyzerResult(CODE, "sell", min(90.0, 50 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class MacdSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
