"""Opening Range Breakout (ORB) — first 30/60 minutes range; long break of high, short break of low.

For 15m bars: first 4 bars of session = 1 hour ORB.
For other granularities: take first 4 bars of the most recent session start (UTC midnight).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "opening_range_breakout"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    today = df.index[-1].normalize()
    today_df = df[df.index >= today]
    if len(today_df) < 5:
        # session may be empty; use last 24 bars as proxy
        today_df = df.iloc[-24:]
    orb = today_df.iloc[:4]
    orb_high = float(orb["h"].max()); orb_low = float(orb["l"].min())
    after = today_df.iloc[4:]
    if len(after) == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT,
                              {"orb_high": round(orb_high, 5), "orb_low": round(orb_low, 5)})
    last = float(df["c"].iloc[-1])
    broke_up = last > orb_high
    broke_dn = last < orb_low
    # confirmation: post-ORB highest > orb_high
    conf_up = float(after["h"].max()) > orb_high and last > orb_high
    conf_dn = float(after["l"].min()) < orb_low and last < orb_low
    payload = {"orb_high": round(orb_high, 5), "orb_low": round(orb_low, 5),
               "broke_up": broke_up, "broke_down": broke_dn,
               "confirmed_up": conf_up, "confirmed_down": conf_dn}
    if conf_up: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if conf_dn: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if broke_up: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if broke_dn: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class OpeningRangeBreakoutAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
