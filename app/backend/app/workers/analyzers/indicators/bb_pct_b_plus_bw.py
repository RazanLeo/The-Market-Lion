"""Bollinger Composite — %B + bandwidth percentile rank.

Combines two BB metrics:
  %B = (close - lower) / (upper - lower)
  Bandwidth = (upper - lower) / SMA20
  BW Rank = percentile of current BW vs last 100 BW values
A "low BW + extreme %B" combination is a high-probability mean-reversion setup.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "bb_pct_b_plus_bw"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 100:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    sma = c.rolling(20).mean()
    sd = c.rolling(20).std()
    upper = sma + 2 * sd
    lower = sma - 2 * sd
    pct_b = (c - lower) / (upper - lower + 1e-9)
    bw = (upper - lower) / (sma + 1e-9)
    bw_w = bw.iloc[-100:].dropna()
    cur_bw = float(bw.iloc[-1] or 0)
    bw_rank = float((bw_w <= cur_bw).sum() / max(len(bw_w), 1))
    cur_pct_b = float(pct_b.iloc[-1])
    payload = {"pct_b": round(cur_pct_b, 3), "bandwidth": round(cur_bw, 4),
               "bw_percentile": round(bw_rank, 3)}
    if cur_pct_b > 1.0 and bw_rank > 0.7:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if cur_pct_b < 0.0 and bw_rank > 0.7:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if bw_rank < 0.15 and cur_pct_b > 0.5:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)  # squeeze upward
    if bw_rank < 0.15 and cur_pct_b < 0.5:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class BbPctBPlusBwAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
