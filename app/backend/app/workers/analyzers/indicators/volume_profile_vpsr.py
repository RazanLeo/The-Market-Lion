"""Volume Profile - Session Range (VPSR).

Computes volume profile per UTC session (calendar day). Returns POC of the most-recent
completed session and tests close proximity to it. Buy if close re-enters from below
the previous session's POC (acceptance), sell if rejected from above.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "volume_profile_vpsr"
WEIGHT_DEFAULT = 1.0
N_BINS = 24


def _session_poc(sub: pd.DataFrame) -> float:
    lo = float(sub["l"].min()); hi = float(sub["h"].max())
    if hi <= lo: return float(sub["c"].iloc[-1])
    typical = (sub["h"] + sub["l"] + sub["c"]) / 3
    bins = np.zeros(N_BINS)
    for tp, vol in zip(typical.values, sub["v"].values):
        idx = min(N_BINS - 1, max(0, int((tp - lo) / (hi - lo) * N_BINS)))
        bins[idx] += float(vol)
    poc_idx = int(np.argmax(bins))
    return float(lo + (poc_idx + 0.5) * (hi - lo) / N_BINS)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    df2 = df.copy()
    df2["session"] = df2.index.floor("D")
    sessions = list(df2["session"].unique())
    if len(sessions) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    prev_session_id = sessions[-2]
    prev_session = df2[df2["session"] == prev_session_id]
    cur_session = df2[df2["session"] == sessions[-1]]
    if len(prev_session) < 5 or len(cur_session) < 1:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    prev_poc = _session_poc(prev_session)
    cur_poc = _session_poc(cur_session) if len(cur_session) >= 5 else None
    last_c = float(df["c"].iloc[-1])
    rng = float(prev_session["h"].max() - prev_session["l"].min()) + 1e-9
    payload = {"prev_session_poc": round(prev_poc, 5),
               "cur_session_poc": round(cur_poc, 5) if cur_poc else None,
               "last_close": round(last_c, 5)}
    diff_pct = abs(last_c - prev_poc) / rng
    if diff_pct < 0.05 and last_c > prev_poc:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if diff_pct < 0.05 and last_c < prev_poc:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VolumeProfileVpsrAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
