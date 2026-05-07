"""Harmonic Patterns School — multi-pattern harmonic recognition (Gartley/Bat/Crab).

For the most-recent 5 swing pivots (X, A, B, C, D) checks fib ratios against patterns:
  Gartley: AB=0.618×XA, BC=0.382-0.886×AB, CD=1.272-1.618×BC, AD=0.786×XA
  Bat:     AB=0.382-0.5×XA, BC=0.382-0.886×AB, CD=1.618-2.618×BC, AD=0.886×XA
  Crab:    AB=0.382-0.618×XA, BC=0.382-0.886×AB, CD=2.618-3.618×BC, AD=1.618×XA
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "harmonic_patterns_school"
WEIGHT_DEFAULT = 1.05


def _swing_pivots(df, n=3):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def _ratio_match(actual, target_min, target_max, tol=0.05):
    return target_min - tol <= actual <= target_max + tol


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swing_pivots(df, 3)
    if len(pivs) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last5 = pivs[-5:]
    X, A, B, C, D = last5
    xa = abs(A[2] - X[2]); ab = abs(B[2] - A[2])
    bc = abs(C[2] - B[2]); cd = abs(D[2] - C[2])
    ad = abs(D[2] - A[2])
    if xa <= 0 or ab <= 0 or bc <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ab_xa = ab / xa; bc_ab = bc / ab; cd_bc = cd / bc; ad_xa = ad / xa
    pattern = None; bullish = X[1] == "L" and A[1] == "H" and D[1] == "L"
    bearish = X[1] == "H" and A[1] == "L" and D[1] == "H"
    if _ratio_match(ab_xa, 0.618, 0.618) and _ratio_match(cd_bc, 1.272, 1.618) and _ratio_match(ad_xa, 0.786, 0.786):
        pattern = "Gartley"
    elif _ratio_match(ab_xa, 0.382, 0.5) and _ratio_match(cd_bc, 1.618, 2.618) and _ratio_match(ad_xa, 0.886, 0.886):
        pattern = "Bat"
    elif _ratio_match(ab_xa, 0.382, 0.618) and _ratio_match(cd_bc, 2.618, 3.618) and _ratio_match(ad_xa, 1.618, 1.618):
        pattern = "Crab"
    payload = {"pattern": pattern, "bullish": bullish, "bearish": bearish,
               "ab/xa": round(ab_xa, 3), "cd/bc": round(cd_bc, 3), "ad/xa": round(ad_xa, 3)}
    if pattern and bullish:
        return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if pattern and bearish:
        return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class HarmonicPatternsSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
