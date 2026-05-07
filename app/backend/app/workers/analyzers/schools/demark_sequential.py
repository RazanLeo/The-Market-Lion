"""DeMark Sequential — pure TD Sequential 1-9 + 8/9 setups.

Setup count: 9 consecutive closes greater than close 4 bars ago = bearish setup.
Mirror for bullish. Confirmed reversal at 9/9 + qualified close.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "demark_sequential"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    bull_count = bear_count = 0
    bull_streak = []  # list of consecutive c>c[-4]
    bear_streak = []
    for i in range(4, len(c)):
        c_now = float(c.iloc[i]); c_prior = float(c.iloc[i - 4])
        if c_now < c_prior:
            bull_count += 1
            if bull_count > 9: bull_count = 1
        else:
            bull_count = 0
        if c_now > c_prior:
            bear_count += 1
            if bear_count > 9: bear_count = 1
        else:
            bear_count = 0
    perfect_bull = bull_count == 9 and float(df["l"].iloc[-1]) <= float(df["l"].iloc[-3]) and \
                   float(df["l"].iloc[-1]) <= float(df["l"].iloc[-2])
    perfect_bear = bear_count == 9 and float(df["h"].iloc[-1]) >= float(df["h"].iloc[-3]) and \
                   float(df["h"].iloc[-1]) >= float(df["h"].iloc[-2])
    payload = {"bull_setup_count": bull_count, "bear_setup_count": bear_count,
               "perfected_bull9": perfect_bull, "perfected_bear9": perfect_bear}
    if perfect_bull:
        return AnalyzerResult(CODE, "buy", 85, WEIGHT_DEFAULT, payload)
    if perfect_bear:
        return AnalyzerResult(CODE, "sell", 85, WEIGHT_DEFAULT, payload)
    if bull_count >= 8:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if bear_count >= 8:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class DemarkSequentialAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
