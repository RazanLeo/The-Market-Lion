"""Vortex Indicator — VI+ and VI- with cross detection and trend strength assessment.

Period 14:
   VM+ = |H[t] - L[t-1]|
   VM- = |L[t] - H[t-1]|
   TR  = max(H[t]-L[t], |H[t]-C[t-1]|, |L[t]-C[t-1]|)
   VI+ = sum(VM+, 14) / sum(TR, 14)
   VI- = sum(VM-, 14) / sum(TR, 14)
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "vortex_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    vm_plus = (h - l.shift()).abs()
    vm_minus = (l - h.shift()).abs()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    sum_tr = tr.rolling(14).sum()
    vi_plus = vm_plus.rolling(14).sum() / sum_tr.replace(0, 1e-9)
    vi_minus = vm_minus.rolling(14).sum() / sum_tr.replace(0, 1e-9)

    last_p = float(vi_plus.iloc[-1]); prev_p = float(vi_plus.iloc[-2])
    last_m = float(vi_minus.iloc[-1]); prev_m = float(vi_minus.iloc[-2])
    cross_up = prev_p <= prev_m and last_p > last_m
    cross_dn = prev_p >= prev_m and last_p < last_m
    diff = last_p - last_m
    payload = {"VI+": round(last_p, 3), "VI-": round(last_m, 3),
               "diff": round(diff, 3), "cross_up": cross_up, "cross_down": cross_dn}
    if cross_up: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if cross_dn: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if diff > 0.1: return AnalyzerResult(CODE, "buy", min(60, 30 + diff * 200), WEIGHT_DEFAULT, payload)
    if diff < -0.1: return AnalyzerResult(CODE, "sell", min(60, 30 + abs(diff) * 200), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VortexSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
