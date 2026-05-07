"""Auction Market Theory — Volume Profile shape detection (D / P / b) + value area + failed auctions."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "auction_market_theory"
WEIGHT_DEFAULT = 1.2


def _build_profile(df: pd.DataFrame, bins: int = 30):
    weights = df["v"].fillna(1).to_numpy() if "v" in df.columns else np.ones(len(df))
    prices = ((df["h"] + df["l"]) / 2).to_numpy()
    if len(prices) == 0: return np.array([]), np.array([])
    hist, edges = np.histogram(prices, bins=bins, weights=weights)
    return hist, edges


def _value_area(hist, edges, pct: float = 0.70):
    if hist.sum() == 0: return None, None, None
    poc_idx = int(hist.argmax())
    target = hist.sum() * pct; cur = hist[poc_idx]
    lo = hi = poc_idx
    while cur < target and (lo > 0 or hi < len(hist) - 1):
        next_lo = hist[lo - 1] if lo > 0 else 0
        next_hi = hist[hi + 1] if hi < len(hist) - 1 else 0
        if next_lo >= next_hi and lo > 0:
            lo -= 1; cur += next_lo
        elif hi < len(hist) - 1:
            hi += 1; cur += next_hi
        else:
            lo -= 1; cur += next_lo
    return float((edges[poc_idx] + edges[poc_idx + 1]) / 2), float(edges[lo]), float(edges[hi + 1])


def _profile_shape(hist) -> str:
    if len(hist) < 5 or hist.sum() == 0: return "unknown"
    third = len(hist) // 3
    top = hist[2 * third:].sum(); mid = hist[third:2 * third].sum(); bot = hist[:third].sum()
    total = hist.sum()
    top_p, mid_p, bot_p = top / total, mid / total, bot / total
    if mid_p >= 0.45 and abs(top_p - bot_p) < 0.15: return "D"
    if top_p > 0.45 and bot_p < 0.20: return "P_buying_tail"
    if bot_p > 0.45 and top_p < 0.20: return "b_selling_tail"
    return "unbalanced"


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    today = df.index[-1].normalize() if isinstance(df.index, pd.DatetimeIndex) else None
    if today is not None:
        today_df = df[df.index >= today]
        prev_df = df[(df.index >= today - pd.Timedelta(days=1)) & (df.index < today)]
    else:
        today_df = df.iloc[-96:]; prev_df = df.iloc[-192:-96]

    hist_t, edges_t = _build_profile(today_df, bins=30)
    if hist_t.size == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    poc_t, va_lo_t, va_hi_t = _value_area(hist_t, edges_t)
    shape_t = _profile_shape(hist_t)

    failed_auction = None
    if len(prev_df) > 10:
        hist_p, edges_p = _build_profile(prev_df, bins=30)
        _, va_lo_p, va_hi_p = _value_area(hist_p, edges_p)
        if va_lo_p and va_hi_p:
            today_high = float(today_df["h"].max()); today_low = float(today_df["l"].min())
            last_close = float(df["c"].iloc[-1])
            if today_high > va_hi_p and last_close < va_hi_p:
                failed_auction = {"direction": "failed_above_VAH", "VAH": round(va_hi_p, 5)}
            elif today_low < va_lo_p and last_close > va_lo_p:
                failed_auction = {"direction": "failed_below_VAL", "VAL": round(va_lo_p, 5)}

    last_close = float(df["c"].iloc[-1])
    in_value = (va_lo_t is not None) and (va_lo_t <= last_close <= va_hi_t)

    payload = {"shape": shape_t, "poc": round(poc_t, 5) if poc_t else None,
               "VAH": round(va_hi_t, 5) if va_hi_t else None,
               "VAL": round(va_lo_t, 5) if va_lo_t else None,
               "in_value_area": in_value, "failed_auction": failed_auction}

    score = 0.0
    if va_lo_t and last_close <= va_lo_t * 1.001: score += 15
    if va_hi_t and last_close >= va_hi_t * 0.999: score -= 15
    if shape_t == "P_buying_tail": score += 25
    if shape_t == "b_selling_tail": score -= 25
    if failed_auction and failed_auction["direction"] == "failed_above_VAH": score -= 30
    if failed_auction and failed_auction["direction"] == "failed_below_VAL": score += 30

    if score >= 20:
        return AnalyzerResult(CODE, "buy", min(85.0, 50 + score), WEIGHT_DEFAULT, payload)
    if score <= -20:
        return AnalyzerResult(CODE, "sell", min(85.0, 50 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class AuctionMarketTheoryAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
