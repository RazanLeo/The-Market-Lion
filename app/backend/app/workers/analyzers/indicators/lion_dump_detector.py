"""Lion DUMP Detector — sudden downward spike (mirror of BUMP).

Trigger: ROC(3) < 5th percentile of last 100 bars AND close in lower 30% of bar range.
Indicates aggressive selling impulse — potential capitulation or breakdown start.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_dump_detector"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 110:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    roc3 = (c - c.shift(3)) / c.shift(3) * 100
    win = roc3.iloc[-100:].dropna()
    if len(win) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    p5 = float(np.percentile(win, 5))
    cur = float(roc3.iloc[-1])
    rng = float(df["h"].iloc[-1] - df["l"].iloc[-1])
    pos_in_bar = (float(c.iloc[-1]) - float(df["l"].iloc[-1])) / (rng + 1e-9)
    dump = cur < p5 and pos_in_bar < 0.3 and cur < 0
    magnitude = (p5 - cur) / max(abs(p5), 0.01) if dump else 0
    payload = {"roc3": round(cur, 3), "p5": round(p5, 3),
               "pos_in_bar": round(pos_in_bar, 2),
               "dump_active": dump, "magnitude": round(magnitude, 2)}
    if dump:
        return AnalyzerResult(CODE, "sell", min(80, 55 + magnitude * 25), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionDumpDetectorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
