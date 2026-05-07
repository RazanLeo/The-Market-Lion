"""RSI School — Wilder RSI(14) + zone detection + classic & hidden divergence + failure swing + 50-line filter."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "rsi_school"
WEIGHT_DEFAULT = 1.0


def _wilder_rsi(c: pd.Series, period: int = 14) -> pd.Series:
    delta = c.diff()
    up = delta.where(delta > 0, 0); dn = -delta.where(delta < 0, 0)
    avg_up = up.ewm(alpha=1 / period, adjust=False).mean()
    avg_dn = dn.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_up / avg_dn.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]; rsi = _wilder_rsi(c, 14)
    last = float(rsi.iloc[-1]); prev = float(rsi.iloc[-2])
    if last > 70: zone = "overbought"
    elif last < 30: zone = "oversold"
    elif last > 50: zone = "bullish_bias"
    elif last < 50: zone = "bearish_bias"
    else: zone = "neutral"

    win = df.iloc[-30:]; rsi_w = rsi.iloc[-30:]
    p_high = int(win["c"].argmax()); p_low = int(win["c"].argmin())
    bear_div = bull_div = bull_hidden = bear_hidden = False
    if p_high > 5:
        earlier = int(win["c"].iloc[:p_high].argmax())
        if win["c"].iloc[p_high] > win["c"].iloc[earlier] and rsi_w.iloc[p_high] < rsi_w.iloc[earlier]:
            bear_div = True
    if p_low > 5:
        earlier = int(win["c"].iloc[:p_low].argmin())
        if win["c"].iloc[p_low] < win["c"].iloc[earlier] and rsi_w.iloc[p_low] > rsi_w.iloc[earlier]:
            bull_div = True
    if p_high > 5:
        earlier = int(win["c"].iloc[:p_high].argmax())
        if win["c"].iloc[p_high] < win["c"].iloc[earlier] and rsi_w.iloc[p_high] > rsi_w.iloc[earlier]:
            bear_hidden = True
    if p_low > 5:
        earlier = int(win["c"].iloc[:p_low].argmin())
        if win["c"].iloc[p_low] > win["c"].iloc[earlier] and rsi_w.iloc[p_low] < rsi_w.iloc[earlier]:
            bull_hidden = True

    last_50 = rsi.iloc[-30:]
    failure_bull = (last_50.min() < 30) and (last_50.iloc[-1] > 30) and (last_50.iloc[-1] > last_50.iloc[-10:-3].max())
    failure_bear = (last_50.max() > 70) and (last_50.iloc[-1] < 70) and (last_50.iloc[-1] < last_50.iloc[-10:-3].min())

    payload = {"rsi": round(last, 2), "rsi_prev": round(prev, 2), "zone": zone,
               "bull_div_classic": bull_div, "bear_div_classic": bear_div,
               "bull_div_hidden": bull_hidden, "bear_div_hidden": bear_hidden,
               "failure_swing_bull": failure_bull, "failure_swing_bear": failure_bear}
    score = 0.0
    if bull_div: score += 35
    if bear_div: score -= 35
    if bull_hidden: score += 18
    if bear_hidden: score -= 18
    if failure_bull: score += 25
    if failure_bear: score -= 25
    if zone == "oversold" and prev < last: score += 18
    if zone == "overbought" and prev > last: score -= 18
    if zone == "bullish_bias": score += 5
    if zone == "bearish_bias": score -= 5

    if score >= 22:
        return AnalyzerResult(CODE, "buy", min(90.0, 50 + score), WEIGHT_DEFAULT, payload)
    if score <= -22:
        return AnalyzerResult(CODE, "sell", min(90.0, 50 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class RsiSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
