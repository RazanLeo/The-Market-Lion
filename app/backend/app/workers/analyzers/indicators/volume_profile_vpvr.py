"""Volume Profile - Visible Range (VPVR).

Bins last N bars' price range into 30 buckets and sums volume per bucket. Identifies
Point of Control (POC = bin with highest volume), and Value Area (70% of total volume
around POC). Buy if close near VAL (Value Area Low), sell if near VAH (Value Area High).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "volume_profile_vpvr"
WEIGHT_DEFAULT = 1.1
N_BINS = 30
VA_PCT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-200:] if len(df) > 200 else df
    lo = float(win["l"].min()); hi = float(win["h"].max())
    if hi <= lo:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    edges = np.linspace(lo, hi, N_BINS + 1)
    typical = (win["h"] + win["l"] + win["c"]) / 3
    vol_per_bin = np.zeros(N_BINS)
    for tp, vol in zip(typical.values, win["v"].values):
        idx = min(N_BINS - 1, max(0, int((tp - lo) / (hi - lo) * N_BINS)))
        vol_per_bin[idx] += float(vol)
    poc_idx = int(np.argmax(vol_per_bin))
    poc_price = float((edges[poc_idx] + edges[poc_idx + 1]) / 2)
    total = vol_per_bin.sum()
    target = total * VA_PCT
    cumulative = vol_per_bin[poc_idx]
    lo_i = hi_i = poc_idx
    while cumulative < target and (lo_i > 0 or hi_i < N_BINS - 1):
        below = vol_per_bin[lo_i - 1] if lo_i > 0 else 0
        above = vol_per_bin[hi_i + 1] if hi_i < N_BINS - 1 else 0
        if below >= above and lo_i > 0:
            lo_i -= 1; cumulative += below
        elif hi_i < N_BINS - 1:
            hi_i += 1; cumulative += above
        else:
            break
    vah = float(edges[hi_i + 1]); val = float(edges[lo_i])
    last_c = float(df["c"].iloc[-1])
    rng = hi - lo
    payload = {"poc": round(poc_price, 5), "vah": round(vah, 5), "val": round(val, 5),
               "n_bins": N_BINS, "value_area_pct": VA_PCT}
    if abs(last_c - val) < rng * 0.02:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if abs(last_c - vah) < rng * 0.02:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if abs(last_c - poc_price) < rng * 0.01:
        return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VolumeProfileVpvrAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
