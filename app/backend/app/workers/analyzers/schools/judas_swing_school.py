"""Judas Swing (ICT) — false move at session open then opposite move.

Detect within the first 4 bars after London open (07:00 UTC) and NY open (13:30 UTC):
A spike high or low that is then reversed by ≥ 2× the spike size within next 6 bars.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "judas_swing_school"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 96 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    today = df.index[-1].normalize()
    london_open = today + pd.Timedelta(hours=7)
    ny_open = today + pd.Timedelta(hours=13, minutes=30)
    out_signal = None
    setup = []
    for label, t0 in [("London", london_open), ("NY", ny_open)]:
        sess = df[(df.index >= t0) & (df.index <= t0 + pd.Timedelta(hours=2, minutes=30))]
        if len(sess) < 6: continue
        first4 = sess.iloc[:4]
        post = sess.iloc[4:]
        open_p = float(first4["o"].iloc[0])
        spike_high = float(first4["h"].max()); spike_low = float(first4["l"].min())
        spike_up_size = spike_high - open_p
        spike_dn_size = open_p - spike_low
        # Reversal after spike
        post_low = float(post["l"].min()); post_high = float(post["h"].max())
        if spike_up_size > 0 and (open_p - post_low) > 2 * spike_up_size:
            setup.append({"session": label, "type": "false_high_then_dn",
                          "spike_high": spike_high, "post_low": post_low})
            out_signal = "sell"
        if spike_dn_size > 0 and (post_high - open_p) > 2 * spike_dn_size:
            setup.append({"session": label, "type": "false_low_then_up",
                          "spike_low": spike_low, "post_high": post_high})
            out_signal = "buy"
    payload = {"setups": setup}
    if out_signal == "buy": return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if out_signal == "sell": return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class JudasSwingSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
