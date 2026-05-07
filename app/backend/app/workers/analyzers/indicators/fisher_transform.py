"""Fisher Transform of normalized price. Maps to gaussian-like distribution.

x = 2 × (price-position-in-range) - 1, clipped to [-0.999, 0.999].
fisher = 0.5 × ln((1+x)/(1-x)).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "fisher_transform"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ll = df["l"].rolling(10).min(); hh = df["h"].rolling(10).max()
    pos = (df["c"] - ll) / (hh - ll + 1e-9)
    x = (2 * pos - 1).clip(-0.999, 0.999)
    fish = 0.5 * np.log((1 + x) / (1 - x))
    last = float(fish.iloc[-1]); prev = float(fish.iloc[-2])
    payload = {"fisher": round(last, 3)}
    if last > 1.5: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if last < -1.5: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last > 0 and prev < 0: return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if last < 0 and prev > 0: return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class FisherTransformIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
