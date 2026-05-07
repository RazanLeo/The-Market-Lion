"""Liquidity Theory — map equal-highs (BSL) and equal-lows (SSL) clusters.

External liquidity: clusters at the most recent major swing.
Internal liquidity: clusters between recent swings.
Tolerance for "equal" = 0.2×ATR.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "liquidity_theory"
WEIGHT_DEFAULT = 1.0


def _swings(df: pd.DataFrame, n: int = 3):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def _equal_clusters(prices: list[float], tol: float, min_size: int = 2):
    sp = sorted(prices)
    if not sp: return []
    clusters = [[sp[0]]]
    for p in sp[1:]:
        if abs(p - clusters[-1][-1]) <= tol: clusters[-1].append(p)
        else: clusters.append([p])
    return [c for c in clusters if len(c) >= min_size]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    pivs = _swings(df, 3)
    highs = [p[2] for p in pivs if p[1] == "H"]
    lows = [p[2] for p in pivs if p[1] == "L"]
    bsl = _equal_clusters(highs, atr * 0.2, 2)
    ssl = _equal_clusters(lows, atr * 0.2, 2)
    bsl_levels = [round(sum(c) / len(c), 5) for c in bsl]
    ssl_levels = [round(sum(c) / len(c), 5) for c in ssl]
    last = float(df["c"].iloc[-1])
    last_high = float(df["h"].iloc[-1]); last_low = float(df["l"].iloc[-1])
    nearest_bsl = min((p for p in bsl_levels if p > last), default=None)
    nearest_ssl = max((p for p in ssl_levels if p < last), default=None)
    # Detect taken liquidity
    taken_bsl = nearest_bsl and last_high >= nearest_bsl and last < nearest_bsl
    taken_ssl = nearest_ssl and last_low <= nearest_ssl and last > nearest_ssl
    payload = {"BSL_levels": bsl_levels[-5:], "SSL_levels": ssl_levels[-5:],
               "nearest_BSL_above": nearest_bsl, "nearest_SSL_below": nearest_ssl,
               "taken_BSL_now": taken_bsl, "taken_SSL_now": taken_ssl}
    if taken_ssl: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if taken_bsl: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LiquidityTheoryAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
