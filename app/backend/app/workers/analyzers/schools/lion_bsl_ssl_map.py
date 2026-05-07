"""Lion BSL/SSL Map — clusters of equal highs (BSL) and equal lows (SSL) within 0.2×ATR.

For each cluster of ≥2 swings: mark as 'active' if no wick has pierced; 'taken' if wicked.
Identify nearest active level above (BSL) and below (SSL). Detect when price has just taken
a level (intra-bar) → expect retracement.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_bsl_ssl_map"
WEIGHT_DEFAULT = 1.0


def _swings(df: pd.DataFrame, n: int = 3):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def _cluster(items: list[tuple[int, float]], tol: float):
    sp = sorted(items, key=lambda x: x[1])
    if not sp: return []
    clusters = [[sp[0]]]
    for it in sp[1:]:
        if abs(it[1] - clusters[-1][-1][1]) <= tol: clusters[-1].append(it)
        else: clusters.append([it])
    return [c for c in clusters if len(c) >= 2]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    pivs = _swings(df, 3)
    high_items = [(p[0], p[2]) for p in pivs if p[1] == "H"]
    low_items = [(p[0], p[2]) for p in pivs if p[1] == "L"]
    bsl = _cluster(high_items, atr * 0.2)
    ssl = _cluster(low_items, atr * 0.2)
    last_close = float(df["c"].iloc[-1])
    last_high = float(df["h"].iloc[-1]); last_low = float(df["l"].iloc[-1])
    bsl_states = []
    for cl in bsl:
        avg_p = sum(x[1] for x in cl) / len(cl)
        last_idx = max(x[0] for x in cl)
        post = df.iloc[last_idx + 1:]
        taken = bool(len(post) and post["h"].max() > avg_p)
        bsl_states.append({"price": round(avg_p, 5), "touches": len(cl), "taken": taken})
    ssl_states = []
    for cl in ssl:
        avg_p = sum(x[1] for x in cl) / len(cl)
        last_idx = max(x[0] for x in cl)
        post = df.iloc[last_idx + 1:]
        taken = bool(len(post) and post["l"].min() < avg_p)
        ssl_states.append({"price": round(avg_p, 5), "touches": len(cl), "taken": taken})
    active_bsl = [b for b in bsl_states if not b["taken"] and b["price"] > last_close]
    active_ssl = [s for s in ssl_states if not s["taken"] and s["price"] < last_close]
    nearest_bsl = min(active_bsl, key=lambda x: x["price"]) if active_bsl else None
    nearest_ssl = max(active_ssl, key=lambda x: x["price"]) if active_ssl else None
    just_took_bsl = any(b for b in bsl_states if last_high >= b["price"] and last_close < b["price"])
    just_took_ssl = any(s for s in ssl_states if last_low <= s["price"] and last_close > s["price"])
    payload = {"BSL_count": len(bsl_states), "SSL_count": len(ssl_states),
               "nearest_active_BSL": nearest_bsl, "nearest_active_SSL": nearest_ssl,
               "just_took_BSL": just_took_bsl, "just_took_SSL": just_took_ssl}
    if just_took_ssl: return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if just_took_bsl: return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionBslSslMapAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
