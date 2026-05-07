"""Horizontal Volume Profile — POC, VAH/VAL, HVN/LVN over last 100 bars.

Each bar contributes its volume distributed evenly across [low, high].
Bins = 30. Value Area = the contiguous bins around POC accumulating ≥70% of total.
HVN = bins above 1.5× mean. LVN = bins below 0.5× mean.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "volume_profile_horizontal"
WEIGHT_DEFAULT = 1.0


def _profile(df: pd.DataFrame, bins: int = 30):
    if "v" not in df.columns:
        v = pd.Series(1.0, index=df.index)
    else:
        v = df["v"].fillna(1.0)
    lo = float(df["l"].min()); hi = float(df["h"].max())
    if hi <= lo:
        return None
    edges = np.linspace(lo, hi, bins + 1)
    vol = np.zeros(bins, dtype=float)
    for i in range(len(df)):
        bar_lo = float(df["l"].iloc[i]); bar_hi = float(df["h"].iloc[i])
        bar_v = float(v.iloc[i])
        if bar_hi <= bar_lo: continue
        first = max(0, np.searchsorted(edges, bar_lo, side="right") - 1)
        last = min(bins - 1, np.searchsorted(edges, bar_hi, side="right") - 1)
        span = max(last - first + 1, 1)
        per_bin = bar_v / span
        vol[first:last + 1] += per_bin
    return vol, edges


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    win = df.iloc[-100:] if len(df) >= 100 else df
    if len(win) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    res = _profile(win, bins=30)
    if res is None:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    vol, edges = res
    poc_idx = int(vol.argmax())
    poc = float((edges[poc_idx] + edges[poc_idx + 1]) / 2)
    target = vol.sum() * 0.70
    cur = vol[poc_idx]; lo, hi = poc_idx, poc_idx
    while cur < target and (lo > 0 or hi < len(vol) - 1):
        lv = vol[lo - 1] if lo > 0 else -1
        rv = vol[hi + 1] if hi < len(vol) - 1 else -1
        if lv >= rv and lo > 0: lo -= 1; cur += vol[lo]
        elif hi < len(vol) - 1: hi += 1; cur += vol[hi]
        else: break
    val = float(edges[lo]); vah = float(edges[hi + 1])
    mean_vol = float(vol.mean())
    hvn = [float((edges[i] + edges[i + 1]) / 2) for i in range(len(vol)) if vol[i] > mean_vol * 1.5]
    lvn = [float((edges[i] + edges[i + 1]) / 2) for i in range(len(vol)) if vol[i] < mean_vol * 0.5]
    last = float(df["c"].iloc[-1])
    in_value = val <= last <= vah
    payload = {"POC": round(poc, 5), "VAH": round(vah, 5), "VAL": round(val, 5),
               "HVN_levels": [round(x, 5) for x in hvn][:5],
               "LVN_levels": [round(x, 5) for x in lvn][:5],
               "in_value_area": in_value}
    if last < val: return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if last > vah: return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VolumeProfileHorizontalAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
