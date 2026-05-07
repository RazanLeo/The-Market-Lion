"""A/D Line proxy on single instrument: cumulative (up_bars - down_bars) over time."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "advance_decline_line"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sgn = np.sign(df["c"].diff().fillna(0))
    ad = sgn.cumsum()
    last = float(ad.iloc[-1]); prev = float(ad.iloc[-30])
    rising = last > prev
    payload = {"ad_line_proxy": round(last, 0), "rising_30bars": rising}
    if rising: return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
class AdvanceDeclineLineIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
