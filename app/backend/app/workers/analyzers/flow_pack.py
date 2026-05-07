"""Flow analyzers — Volume Profile (POC/HVN/LVN), Order Flow basics, Bookmap basics."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..engines.voting_engine import AnalyzerResult


def volume_profile_analyzer(df: pd.DataFrame, bins: int = 30) -> AnalyzerResult:
    if len(df) < 50 or "v" not in df.columns:
        return AnalyzerResult("volume_profile", "neutral", 0, 1.0, {})
    win = df.iloc[-200:] if len(df) > 200 else df
    prices = (win["h"] + win["l"]) / 2
    hist, edges = np.histogram(prices, bins=bins, weights=win["v"].fillna(1.0))
    if hist.sum() == 0:
        return AnalyzerResult("volume_profile", "neutral", 0, 1.0, {})
    poc_idx = int(hist.argmax())
    poc = float((edges[poc_idx] + edges[poc_idx + 1]) / 2)
    last = float(df["c"].iloc[-1])
    # HVN cluster (top 3 bins)
    top3 = sorted(zip(range(len(hist)), hist), key=lambda x: -x[1])[:3]
    hvn_levels = [(edges[i] + edges[i+1]) / 2 for i, _ in top3]
    # LVN — bottom of frequented bins (gaps in liquidity)
    lvn_idx = int(hist.argmin())
    lvn = float((edges[lvn_idx] + edges[lvn_idx + 1]) / 2)
    payload = {"poc": poc, "hvn_levels": [round(x, 5) for x in hvn_levels], "lvn": lvn}
    if last < poc * 0.998:
        return AnalyzerResult("volume_profile", "buy", 55, 1.0, {**payload, "reason": "below_poc"})
    if last > poc * 1.002:
        return AnalyzerResult("volume_profile", "sell", 55, 1.0, {**payload, "reason": "above_poc"})
    return AnalyzerResult("volume_profile", "neutral", 0, 1.0, payload)


def order_flow_basic_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    """Basic order flow proxy from candle close direction × volume."""
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult("order_flow", "neutral", 0, 1.0, {})
    win = df.iloc[-30:]
    delta = (win["c"] - win["o"]).apply(np.sign) * win["v"].fillna(1.0)
    cvd = delta.cumsum().iloc[-1]
    cvd_prev = delta.cumsum().iloc[-15] if len(delta) > 15 else 0
    rate = cvd - cvd_prev
    if rate > 0:
        return AnalyzerResult("order_flow", "buy", min(70, 30 + abs(rate) / 1000), 1.0, {"cvd": float(cvd), "rate": float(rate)})
    if rate < 0:
        return AnalyzerResult("order_flow", "sell", min(70, 30 + abs(rate) / 1000), 1.0, {"cvd": float(cvd), "rate": float(rate)})
    return AnalyzerResult("order_flow", "neutral", 0, 1.0, {})


def bookmap_basic_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    """Lightweight Bookmap proxy — until L2 stream is connected, infer iceberg/absorption from price/volume divergence."""
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult("bookmap", "neutral", 0, 1.0, {})
    win = df.iloc[-20:]
    body = (win["c"] - win["o"]).abs()
    body_avg = body.rolling(10).mean().iloc[-1]
    last_body = body.iloc[-1]
    last_vol = float(win["v"].iloc[-1] or 1.0)
    avg_vol = float(win["v"].rolling(10).mean().iloc[-1] or 1.0)
    # Absorption: huge volume, tiny body
    if last_vol > avg_vol * 2 and last_body < body_avg * 0.5:
        direction = "buy" if win["c"].iloc[-1] > win["o"].iloc[-1] else "sell"
        return AnalyzerResult("bookmap", direction, 65, 1.0, {"signal": "absorption", "vol_ratio": last_vol / avg_vol})
    # Pump/Dump: huge volume + huge body
    if last_vol > avg_vol * 2 and last_body > body_avg * 2:
        direction = "buy" if win["c"].iloc[-1] > win["o"].iloc[-1] else "sell"
        return AnalyzerResult("bookmap", direction, 75, 1.0, {"signal": "pump" if direction == "buy" else "dump"})
    return AnalyzerResult("bookmap", "neutral", 0, 1.0, {})
