"""Lion BUMP Detector — sudden upward spike.

Trigger: ROC(3) > 95th percentile of last 100 bars AND close in upper 70% of bar range.
Indicates aggressive buying impulse — potential shake-out or short-squeeze start.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_bump_detector"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 110:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    roc3 = (c - c.shift(3)) / c.shift(3) * 100
    win = roc3.iloc[-100:].dropna()
    if len(win) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    p95 = float(np.percentile(win, 95))
    cur = float(roc3.iloc[-1])
    rng = float(df["h"].iloc[-1] - df["l"].iloc[-1])
    pos_in_bar = (float(c.iloc[-1]) - float(df["l"].iloc[-1])) / (rng + 1e-9)
    bump = cur > p95 and pos_in_bar > 0.7 and cur > 0
    magnitude = (cur - p95) / max(p95, 0.01) if bump else 0
    payload = {"roc3": round(cur, 3), "p95": round(p95, 3),
               "pos_in_bar": round(pos_in_bar, 2),
               "bump_active": bump, "magnitude": round(magnitude, 2)}
    if bump:
        return AnalyzerResult(CODE, "buy", min(80, 55 + magnitude * 25), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionBumpDetectorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
