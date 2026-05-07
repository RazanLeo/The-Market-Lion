"""Bollinger School — %B persistence and band-walk regime classification.

Distinct from john_bollinger_school (M-tops/W-bottoms) — focuses on:
  • %B persistence: how many of last 10 bars had %B > 0.8 (band-walk up) or < 0.2 (down)
  • Mean-reversion bias: %B > 1 + closed inside next bar = mean-revert sell signal
  • Bandwidth percentile rank trigger: rank > 80% of last 100 = trend exhaustion
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "bollinger_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 100:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    sma = c.rolling(20).mean()
    sd = c.rolling(20).std()
    upper = sma + 2 * sd; lower = sma - 2 * sd
    pct_b = (c - lower) / (upper - lower + 1e-9)
    last10 = pct_b.iloc[-10:]
    walk_up = int((last10 > 0.8).sum())
    walk_dn = int((last10 < 0.2).sum())
    bw = (upper - lower) / sma
    bw_rank = float((bw.iloc[-100:] <= bw.iloc[-1]).mean())
    last_b = float(pct_b.iloc[-1]); prev_b = float(pct_b.iloc[-2])
    mean_revert_sell = prev_b > 1 and last_b < 1
    mean_revert_buy = prev_b < 0 and last_b > 0
    payload = {"walk_up_count_10b": walk_up, "walk_dn_count_10b": walk_dn,
               "bw_percentile": round(bw_rank, 2), "%B": round(last_b, 3),
               "mean_revert_buy": mean_revert_buy, "mean_revert_sell": mean_revert_sell}
    if mean_revert_buy:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if mean_revert_sell:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if walk_up >= 6 and bw_rank > 0.8:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)  # exhaustion
    if walk_dn >= 6 and bw_rank > 0.8:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if walk_up >= 4:
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if walk_dn >= 4:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class BollingerSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
