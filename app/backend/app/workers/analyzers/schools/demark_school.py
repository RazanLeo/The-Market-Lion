"""TD Sequential (Tom DeMark) — full setup + countdown logic.

Setup buy: 9 consecutive bars where close[i] < close[i-4].
Setup sell: 9 consecutive bars where close[i] > close[i-4].
After completion, Countdown begins: 13 bars where close[i] ≤ low[i-2] (buy) or close[i] ≥ high[i-2] (sell).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "demark_school"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]; h = df["h"]; l = df["l"]
    # TD Buy Setup count (most recent run)
    td_buy = td_sell = 0
    for i in range(len(c) - 1, max(len(c) - 30, 4), -1):
        if c.iloc[i] < c.iloc[i - 4]:
            td_buy += 1
        else:
            break
    for i in range(len(c) - 1, max(len(c) - 30, 4), -1):
        if c.iloc[i] > c.iloc[i - 4]:
            td_sell += 1
        else:
            break

    setup_complete_buy = td_buy >= 9
    setup_complete_sell = td_sell >= 9

    # Countdown (after a setup): scan latest 13 bars
    countdown_buy = countdown_sell = 0
    if setup_complete_buy:
        for i in range(len(c) - 1, max(len(c) - 14, 2), -1):
            if c.iloc[i] <= l.iloc[i - 2]:
                countdown_buy += 1
    if setup_complete_sell:
        for i in range(len(c) - 1, max(len(c) - 14, 2), -1):
            if c.iloc[i] >= h.iloc[i - 2]:
                countdown_sell += 1

    payload = {"td_buy_setup": td_buy, "td_sell_setup": td_sell,
               "setup_complete_buy_9": setup_complete_buy,
               "setup_complete_sell_9": setup_complete_sell,
               "countdown_buy": countdown_buy, "countdown_sell": countdown_sell}

    if countdown_buy >= 13: return AnalyzerResult(CODE, "buy", 90, WEIGHT_DEFAULT, payload)
    if countdown_sell >= 13: return AnalyzerResult(CODE, "sell", 90, WEIGHT_DEFAULT, payload)
    if setup_complete_buy: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if setup_complete_sell: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if td_buy >= 6: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    if td_sell >= 6: return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class DemarkSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
