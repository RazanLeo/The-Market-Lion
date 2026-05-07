"""TPO Market Profile — Time-Price-Opportunity letters per 30-min slot.

Each 30-min period gets a letter (A, B, C, ...). For every price level touched in that
period, that letter is added. The price with most letters = TPO POC. Single-prints (one
letter only) at extremes signal initiative buying/selling.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "tpo_market_profile"
WEIGHT_DEFAULT = 0.8
N_BINS = 30
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-200:] if len(df) > 200 else df
    grouper = win.index.floor("30min")
    groups = list(pd.unique(grouper))[:len(LETTERS)]
    if len(groups) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    lo = float(win["l"].min()); hi = float(win["h"].max())
    if hi <= lo:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    counts = np.zeros(N_BINS)
    bins_letters: list[set] = [set() for _ in range(N_BINS)]
    for letter, g in zip(LETTERS, groups):
        sub = win[grouper == g]
        if not len(sub): continue
        slo = float(sub["l"].min()); shi = float(sub["h"].max())
        lo_idx = max(0, int((slo - lo) / (hi - lo) * N_BINS))
        hi_idx = min(N_BINS - 1, int((shi - lo) / (hi - lo) * N_BINS))
        for b in range(lo_idx, hi_idx + 1):
            bins_letters[b].add(letter); counts[b] += 1
    poc_idx = int(np.argmax(counts))
    poc = float(lo + (poc_idx + 0.5) * (hi - lo) / N_BINS)
    single_prints = [i for i in range(N_BINS) if counts[i] == 1]
    last_c = float(df["c"].iloc[-1])
    near_extreme_high = any(i >= N_BINS - 3 for i in single_prints)
    near_extreme_low = any(i <= 2 for i in single_prints)
    payload = {"poc": round(poc, 5), "n_letters": len(groups),
               "single_prints_count": len(single_prints),
               "single_prints_high": near_extreme_high, "single_prints_low": near_extreme_low,
               "last_close": round(last_c, 5)}
    if near_extreme_low and last_c > poc:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if near_extreme_high and last_c < poc:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class TpoMarketProfileAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
