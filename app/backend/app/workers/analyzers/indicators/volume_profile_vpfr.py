"""Volume Profile - Fixed Range (VPFR) — anchored at last major pivot.

Anchors the volume profile at the most recent dominant swing low and computes
POC + Value Area for the leg from that anchor to the current bar. Useful for
identifying acceptance/rejection in the active leg.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "volume_profile_vpfr"
WEIGHT_DEFAULT = 0.95
N_BINS = 25


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-150:] if len(df) > 150 else df
    anchor = int(win["l"].argmin())
    leg = win.iloc[anchor:]
    if len(leg) < 10:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    lo = float(leg["l"].min()); hi = float(leg["h"].max())
    if hi <= lo:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    typical = (leg["h"] + leg["l"] + leg["c"]) / 3
    bins = np.zeros(N_BINS)
    for tp, vol in zip(typical.values, leg["v"].values):
        idx = min(N_BINS - 1, max(0, int((tp - lo) / (hi - lo) * N_BINS)))
        bins[idx] += float(vol)
    poc_idx = int(np.argmax(bins))
    poc = float(lo + (poc_idx + 0.5) * (hi - lo) / N_BINS)
    last_c = float(df["c"].iloc[-1])
    rng = hi - lo
    above_poc = (last_c - poc) / rng
    payload = {"anchor_bar": int(anchor), "leg_len": len(leg),
               "poc_fixed_range": round(poc, 5), "leg_high": round(hi, 5),
               "leg_low": round(lo, 5), "above_poc_pct": round(above_poc, 3)}
    if above_poc < -0.05 and last_c > float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if above_poc > 0.4:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VolumeProfileVpfrAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
