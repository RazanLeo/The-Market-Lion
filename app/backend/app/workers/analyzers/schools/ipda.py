"""Interbank Price Delivery Algorithm (IPDA) — ICT advanced concept.

Detect daily, weekly, monthly liquidity pools (equal highs/lows clusters).
A pool is "ripe" if multiple swings cluster within 0.2×ATR.
IPDA "reset" = close beyond previous day's range → expect run to next external pool.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "ipda"
WEIGHT_DEFAULT = 0.95


def _swings(df: pd.DataFrame, n: int = 4):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def _cluster(prices: list[float], tol: float):
    sp = sorted(prices)
    clusters = [[sp[0]]] if sp else []
    for p in sp[1:]:
        if abs(p - clusters[-1][-1]) <= tol: clusters[-1].append(p)
        else: clusters.append([p])
    return [c for c in clusters if len(c) >= 2]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    atr = float((h - l).rolling(14).mean().iloc[-1] or 0)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 4)
    high_pool = _cluster([p[2] for p in pivs if p[1] == "H"], atr * 0.2)
    low_pool = _cluster([p[2] for p in pivs if p[1] == "L"], atr * 0.2)
    high_pools = [round(sum(cl) / len(cl), 5) for cl in high_pool]
    low_pools = [round(sum(cl) / len(cl), 5) for cl in low_pool]
    last_close = float(c.iloc[-1])

    # IPDA reset: close beyond previous "day" range — emulate as 96-bar window for 15m
    win = 96 if len(df) >= 96 else 24
    prev_high = float(h.iloc[-2 * win:-win].max())
    prev_low = float(l.iloc[-2 * win:-win].min())
    reset_up = last_close > prev_high
    reset_down = last_close < prev_low

    nearest_above = min((p for p in high_pools if p > last_close), default=None)
    nearest_below = max((p for p in low_pools if p < last_close), default=None)

    payload = {"atr": round(atr, 5),
               "high_pools": high_pools[-5:], "low_pools": low_pools[-5:],
               "prev_window_high": round(prev_high, 5), "prev_window_low": round(prev_low, 5),
               "reset_up": reset_up, "reset_down": reset_down,
               "nearest_BSL_above": nearest_above, "nearest_SSL_below": nearest_below}
    if reset_up and nearest_above:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if reset_down and nearest_below:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class IpdaAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
