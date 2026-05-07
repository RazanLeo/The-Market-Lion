"""AB=CD Pattern — symmetrical 5-point pattern with leg AB approximately equal to CD.

Bullish: A=high, B=low, C=high (lower than A), D=low (lower than B). |AB|≈|CD|, BC retrace 0.382-0.886.
Bearish: A=low, B=high, C=low, D=high. Same ratios.
Time symmetry: bars from A to B should ≈ bars from C to D (within 30%).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "abcd_pattern"
WEIGHT_DEFAULT = 0.95


def _swings(df: pd.DataFrame, n: int = 4):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 4)
    if len(pivs) < 4:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    A, B, C, D = pivs[-4:]
    types = "".join(p[1] for p in pivs[-4:])
    bullish = types == "HLHL"; bearish = types == "LHLH"
    if not (bullish or bearish):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})

    pa, pb, pc, pd_ = A[2], B[2], C[2], D[2]
    AB = abs(pb - pa); BC = abs(pc - pb); CD = abs(pd_ - pc)
    if AB == 0 or BC == 0: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ratio_cdab = CD / AB
    ratio_bcab = BC / AB
    bars_ab = B[0] - A[0]; bars_cd = D[0] - C[0]
    time_sym = abs(bars_ab - bars_cd) / max(bars_ab, 1) < 0.4

    rule_eq = 0.85 <= ratio_cdab <= 1.15
    rule_bc = 0.382 <= ratio_bcab <= 0.886
    if not (rule_eq and rule_bc):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT,
                              {"CD/AB": round(ratio_cdab, 3), "BC/AB": round(ratio_bcab, 3)})

    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    last_close = float(df["c"].iloc[-1])
    in_prz = abs(last_close - pd_) < atr * 0.5

    payload = {"types": types, "CD/AB": round(ratio_cdab, 3),
               "BC/AB": round(ratio_bcab, 3), "time_symmetry": time_sym,
               "PRZ": round(pd_, 5), "in_PRZ": in_prz}
    if not in_prz:
        return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)
    score = 70 + (10 if time_sym else 0)
    if bullish:
        return AnalyzerResult(CODE, "buy", min(85.0, score), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", min(85.0, score), WEIGHT_DEFAULT, payload)


class AbcdPatternAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
