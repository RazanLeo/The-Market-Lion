"""Support / Resistance — clustering swing pivots by price density + strength scoring.

Method:
  1. Collect all swing highs and lows in the last 200 bars.
  2. Cluster prices that fall within 0.5×ATR using a 1D agglomerative approach.
  3. Strength = touches × 0.7 + recency_factor × 0.3 (recency_factor decays with age).
  4. Detect price near a level (< 0.4×ATR) and bias accordingly.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "support_resistance"
WEIGHT_DEFAULT = 1.1


def _swings(df: pd.DataFrame, n: int = 3):
    highs, lows = [], []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            highs.append((i, float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            lows.append((i, float(df["l"].iloc[i])))
    return highs, lows


def _cluster(points: list[tuple[int, float]], tol: float, total_bars: int):
    """Return list of {price, touches, last_idx, recency, strength}."""
    if not points:
        return []
    sorted_p = sorted(points, key=lambda x: x[1])
    clusters = [[sorted_p[0]]]
    for pt in sorted_p[1:]:
        if abs(pt[1] - sorted_p[points.index(pt)][1]) <= tol:
            pass  # placeholder
        if abs(pt[1] - clusters[-1][-1][1]) <= tol:
            clusters[-1].append(pt)
        else:
            clusters.append([pt])
    result = []
    for cluster in clusters:
        prices = [p[1] for p in cluster]
        idxs = [p[0] for p in cluster]
        avg_price = sum(prices) / len(prices)
        last_idx = max(idxs)
        recency = last_idx / total_bars  # 0..1
        touches = len(cluster)
        strength = touches * 0.7 + recency * 30
        result.append({"price": round(avg_price, 5), "touches": touches,
                       "last_idx": last_idx, "recency": round(recency, 3),
                       "strength": round(strength, 1)})
    return result


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    win = df.iloc[-200:] if len(df) > 200 else df
    atr = float((win["h"] - win["l"]).rolling(14).mean().iloc[-1] or 0)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    tol = atr * 0.5

    highs, lows = _swings(win, 3)
    res_clusters = _cluster(highs, tol, len(win))
    sup_clusters = _cluster(lows, tol, len(win))

    # Filter weak clusters
    res_strong = [r for r in res_clusters if r["touches"] >= 2 and r["strength"] >= 5]
    sup_strong = [r for r in sup_clusters if r["touches"] >= 2 and r["strength"] >= 5]

    last_close = float(df["c"].iloc[-1])
    nearest_res = min(res_strong, key=lambda x: abs(x["price"] - last_close)) if res_strong else None
    nearest_sup = min(sup_strong, key=lambda x: abs(x["price"] - last_close)) if sup_strong else None

    near_res = nearest_res and abs(last_close - nearest_res["price"]) < atr * 0.4
    near_sup = nearest_sup and abs(last_close - nearest_sup["price"]) < atr * 0.4
    above_res = nearest_res and last_close > nearest_res["price"] * 1.001
    below_sup = nearest_sup and last_close < nearest_sup["price"] * 0.999

    payload = {
        "resistance_levels": [r["price"] for r in sorted(res_strong, key=lambda x: -x["strength"])[:5]],
        "support_levels": [r["price"] for r in sorted(sup_strong, key=lambda x: -x["strength"])[:5]],
        "nearest_resistance": nearest_res, "nearest_support": nearest_sup,
        "near_resistance": near_res, "near_support": near_sup,
        "broke_above_resistance": above_res, "broke_below_support": below_sup,
        "atr_tolerance": round(atr * 0.4, 5),
    }

    score = 0.0
    if near_sup:
        score += 25 + (nearest_sup["strength"] / 4)
    if near_res:
        score -= 25 + (nearest_res["strength"] / 4)
    if above_res:
        score += 18  # breakout buy
    if below_sup:
        score -= 18  # breakdown sell

    if score >= 18:
        return AnalyzerResult(CODE, "buy", min(85.0, 45 + score), WEIGHT_DEFAULT, payload)
    if score <= -18:
        return AnalyzerResult(CODE, "sell", min(85.0, 45 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class SupportResistanceAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
