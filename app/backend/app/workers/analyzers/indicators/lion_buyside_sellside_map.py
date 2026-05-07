"""Lion Buyside/Sellside Liquidity Map.

Scans last 60 bars for equal highs (BSL = buy-side liquidity above) and equal lows
(SSL = sell-side below) within tolerance 0.2×ATR. Marks each cluster as active (untaken)
or taken (price already swept).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_buyside_sellside_map"
WEIGHT_DEFAULT = 1.05


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def _eq_clusters(values, tol):
    sorted_vals = sorted([(v, i) for i, v in values])
    clusters = []
    cur_v = [sorted_vals[0][0]]; cur_i = [sorted_vals[0][1]]
    for v, i in sorted_vals[1:]:
        if v - cur_v[-1] <= tol:
            cur_v.append(v); cur_i.append(i)
        else:
            if len(cur_v) >= 2:
                clusters.append((sum(cur_v) / len(cur_v), max(cur_i), len(cur_v)))
            cur_v = [v]; cur_i = [i]
    if len(cur_v) >= 2:
        clusters.append((sum(cur_v) / len(cur_v), max(cur_i), len(cur_v)))
    return clusters


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    tol = atr * 0.2
    win = df.iloc[-60:]
    highs = [(float(win["h"].iloc[i]), i) for i in range(len(win))]
    lows = [(float(win["l"].iloc[i]), i) for i in range(len(win))]
    bsl = _eq_clusters(highs, tol)
    ssl = _eq_clusters(lows, tol)
    last_c = float(df["c"].iloc[-1])
    nearest_bsl = min([b for b in bsl if b[0] >= last_c], key=lambda x: x[0], default=None)
    nearest_ssl = max([s for s in ssl if s[0] <= last_c], key=lambda x: x[0], default=None)
    bsl_taken = []
    for b_p, b_i, n in bsl:
        post = win.iloc[b_i + 1:] if b_i + 1 < len(win) else win.iloc[:0]
        bsl_taken.append(bool(len(post) and float(post["h"].max()) > b_p + tol * 0.5))
    ssl_taken = []
    for s_p, s_i, n in ssl:
        post = win.iloc[s_i + 1:] if s_i + 1 < len(win) else win.iloc[:0]
        ssl_taken.append(bool(len(post) and float(post["l"].min()) < s_p - tol * 0.5))
    payload = {"bsl_clusters": [(round(p, 5), n, t) for (p, _, n), t in zip(bsl, bsl_taken)][:5],
               "ssl_clusters": [(round(p, 5), n, t) for (p, _, n), t in zip(ssl, ssl_taken)][:5],
               "nearest_bsl": round(nearest_bsl[0], 5) if nearest_bsl else None,
               "nearest_ssl": round(nearest_ssl[0], 5) if nearest_ssl else None}
    # Bias: price approaches untaken BSL → expect sweep/reversal short
    if nearest_bsl and abs(nearest_bsl[0] - last_c) < tol * 1.5:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if nearest_ssl and abs(last_c - nearest_ssl[0]) < tol * 1.5:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionBuysideSellsideMapAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
