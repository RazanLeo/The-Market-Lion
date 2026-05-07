"""ICT Optimal Trade Entry (OTE) — retracement to 0.62-0.79 of last impulse leg.

Bullish leg = last swing low → swing high. Bearish = last swing high → swing low.
OTE buy zone in bullish leg = swing_low + 0.62*range to swing_low + 0.79*range, i.e. retracement deeper.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "optimal_trade_entry_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-50:]
    h_idx = int(win["h"].argmax()); l_idx = int(win["l"].argmin())
    swing_h = float(win["h"].iloc[h_idx]); swing_l = float(win["l"].iloc[l_idx])
    rng = swing_h - swing_l
    if rng <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_close = float(df["c"].iloc[-1])
    if h_idx > l_idx:
        # bullish leg: retrace from swing_h back toward swing_l
        ote_top = swing_h - rng * 0.62
        ote_bot = swing_h - rng * 0.79
        in_zone = ote_bot <= last_close <= ote_top
        payload = {"leg": "bullish", "swing_low": round(swing_l, 5),
                   "swing_high": round(swing_h, 5),
                   "ote_top_0_62": round(ote_top, 5), "ote_bot_0_79": round(ote_bot, 5),
                   "in_OTE": in_zone}
        if in_zone: return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    else:
        ote_bot = swing_l + rng * 0.62
        ote_top = swing_l + rng * 0.79
        in_zone = ote_bot <= last_close <= ote_top
        payload = {"leg": "bearish", "swing_high": round(swing_h, 5),
                   "swing_low": round(swing_l, 5),
                   "ote_bot_0_62": round(ote_bot, 5), "ote_top_0_79": round(ote_top, 5),
                   "in_OTE": in_zone}
        if in_zone: return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class OptimalTradeEntrySchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
