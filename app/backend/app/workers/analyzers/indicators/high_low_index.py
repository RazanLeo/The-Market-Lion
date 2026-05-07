"""High-Low Index (HLI) — 100 × new highs / (new highs + new lows) over rolling 50.

A bar makes a "new high" when high > rolling 50-bar max excluding self. New low = mirror.
HLI > 70 = strong uptrend, HLI < 30 = strong downtrend. Cross 50 = trend change.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "high_low_index"
WEIGHT_DEFAULT = 0.75


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rolling_max = df["h"].rolling(50).max().shift(1)
    rolling_min = df["l"].rolling(50).min().shift(1)
    new_h = (df["h"] > rolling_max).astype(int)
    new_l = (df["l"] < rolling_min).astype(int)
    nh_sum = new_h.rolling(20).sum()
    nl_sum = new_l.rolling(20).sum()
    hli = (nh_sum / (nh_sum + nl_sum + 1e-9)) * 100
    last = float(hli.iloc[-1]) if not pd.isna(hli.iloc[-1]) else 50.0
    prev = float(hli.iloc[-2]) if not pd.isna(hli.iloc[-2]) else 50.0
    payload = {"hli": round(last, 2), "hli_prev": round(prev, 2),
               "regime": "bullish" if last > 60 else "bearish" if last < 40 else "neutral"}
    if prev < 50 <= last and last > 55:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if prev > 50 >= last and last < 45:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if last > 70:
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if last < 30:
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class HighLowIndexAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
