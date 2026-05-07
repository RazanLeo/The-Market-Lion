"""Larry Williams composite — Williams %R(14) + Ultimate Oscillator + 3-day reversal pattern.

3-day reversal (bullish):
  • Today's open in lower 25% of yesterday's range AND today's close in upper 50% of today's range.
3-day reversal (bearish): mirror.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "larry_williams_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c, o = df["h"], df["l"], df["c"], df["o"]
    # Williams %R(14)
    hh = h.rolling(14).max(); ll = l.rolling(14).min()
    wr = -100 * (hh - c) / (hh - ll + 1e-9)
    last_wr = float(wr.iloc[-1])

    # Ultimate Oscillator (7,14,28)
    bp = c - pd.concat([l, c.shift()], axis=1).min(axis=1)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    avg7 = bp.rolling(7).sum() / tr.rolling(7).sum().replace(0, 1e-9)
    avg14 = bp.rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)
    avg28 = bp.rolling(28).sum() / tr.rolling(28).sum().replace(0, 1e-9)
    uo = 100 * (4 * avg7 + 2 * avg14 + avg28) / 7
    last_uo = float(uo.iloc[-1])

    # 3-day reversal
    prev_l = float(l.iloc[-2]); prev_h = float(h.iloc[-2])
    prev_range = prev_h - prev_l or 1e-9
    today_o = float(o.iloc[-1]); today_l = float(l.iloc[-1]); today_h = float(h.iloc[-1]); today_c = float(c.iloc[-1])
    today_range = today_h - today_l or 1e-9
    open_pos_in_yest = (today_o - prev_l) / prev_range
    close_pos_in_today = (today_c - today_l) / today_range
    bullish_3day = open_pos_in_yest <= 0.25 and close_pos_in_today >= 0.50
    bearish_3day = open_pos_in_yest >= 0.75 and close_pos_in_today <= 0.50

    payload = {"williams_R": round(last_wr, 1), "ultimate_osc": round(last_uo, 1),
               "open_pos_in_yest_range": round(open_pos_in_yest, 3),
               "close_pos_in_today_range": round(close_pos_in_today, 3),
               "bullish_3day_reversal": bullish_3day, "bearish_3day_reversal": bearish_3day}
    score = 0.0
    if last_wr < -80: score += 15
    if last_wr > -20: score -= 15
    if last_uo < 30: score += 12
    if last_uo > 70: score -= 12
    if bullish_3day: score += 35
    if bearish_3day: score -= 35

    if score >= 25: return AnalyzerResult(CODE, "buy", min(85.0, 45 + score), WEIGHT_DEFAULT, payload)
    if score <= -25: return AnalyzerResult(CODE, "sell", min(85.0, 45 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class LarryWilliamsSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
