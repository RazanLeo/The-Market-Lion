"""Auto Support / Resistance — cluster swing pivots into S/R bands.

Detects 5-bar swing highs/lows over last 200 bars, clusters them by proximity (≤ 0.5×ATR),
then ranks clusters by touch count. Top 3 supports below price + top 3 resistances above
price. Buy signal when price tests strongest support, sell at strongest resistance.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "auto_support_resistance"
WEIGHT_DEFAULT = 1.1


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def _cluster(values, tol):
    values = sorted(values)
    clusters = []
    cur = [values[0]]
    for v in values[1:]:
        if v - cur[-1] <= tol:
            cur.append(v)
        else:
            clusters.append((sum(cur) / len(cur), len(cur)))
            cur = [v]
    clusters.append((sum(cur) / len(cur), len(cur)))
    return clusters


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-200:] if len(df) > 200 else df
    atr = _atr(df)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    tol = atr * 0.5
    highs, lows = [], []
    for i in range(2, len(win) - 2):
        if win["h"].iloc[i] == win["h"].iloc[i - 2:i + 3].max():
            highs.append(float(win["h"].iloc[i]))
        if win["l"].iloc[i] == win["l"].iloc[i - 2:i + 3].min():
            lows.append(float(win["l"].iloc[i]))
    if not highs or not lows:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    res_clusters = sorted(_cluster(highs, tol), key=lambda x: -x[1])[:3]
    sup_clusters = sorted(_cluster(lows, tol), key=lambda x: -x[1])[:3]
    last_c = float(df["c"].iloc[-1])
    nearest_sup = max([c for c in sup_clusters if c[0] <= last_c + tol], key=lambda x: x[0], default=None)
    nearest_res = min([c for c in res_clusters if c[0] >= last_c - tol], key=lambda x: x[0], default=None)
    payload = {"resistances": [(round(p, 5), n) for p, n in res_clusters],
               "supports": [(round(p, 5), n) for p, n in sup_clusters],
               "nearest_sup": (round(nearest_sup[0], 5), nearest_sup[1]) if nearest_sup else None,
               "nearest_res": (round(nearest_res[0], 5), nearest_res[1]) if nearest_res else None}
    if nearest_sup and abs(last_c - nearest_sup[0]) < tol * 0.4 and nearest_sup[1] >= 2:
        return AnalyzerResult(CODE, "buy", min(85, 50 + nearest_sup[1] * 8), WEIGHT_DEFAULT, payload)
    if nearest_res and abs(last_c - nearest_res[0]) < tol * 0.4 and nearest_res[1] >= 2:
        return AnalyzerResult(CODE, "sell", min(85, 50 + nearest_res[1] * 8), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AutoSupportResistanceAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
