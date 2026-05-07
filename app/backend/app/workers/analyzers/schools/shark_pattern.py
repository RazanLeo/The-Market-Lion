"""Shark Pattern (Scott Carney) — XABCD harmonic:
  AB = 1.13 – 1.618  of XA
  BC = 1.13 – 1.618  of AB
  CD = 0.886 – 1.13  of AB
PRZ at D = expected reversal zone.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "shark_pattern"
WEIGHT_DEFAULT = 1.0


def _swings(df: pd.DataFrame, n: int = 4):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 4)
    if len(pivs) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last5 = pivs[-5:]
    types = "".join(p[1] for p in last5)
    bullish = types == "LHLHL"; bearish = types == "HLHLH"
    if not (bullish or bearish):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})
    X, A, B, C, D = (p[2] for p in last5)
    XA = abs(A - X); AB = abs(B - A); BC = abs(C - B); CD = abs(D - C)
    if XA == 0 or AB == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ab_xa = AB / XA; bc_ab = BC / AB; cd_ab = CD / AB

    rule_ab = 1.13 <= ab_xa <= 1.618
    rule_bc = 1.13 <= bc_ab <= 1.618
    rule_cd = 0.886 <= cd_ab <= 1.13
    score = sum([rule_ab, rule_bc, rule_cd])

    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    last_close = float(df["c"].iloc[-1])
    in_prz = abs(last_close - D) < atr * 0.4

    payload = {
        "AB/XA": round(ab_xa, 3), "BC/AB": round(bc_ab, 3), "CD/AB": round(cd_ab, 3),
        "rule_ab": rule_ab, "rule_bc": rule_bc, "rule_cd": rule_cd, "rules_passed": score,
        "PRZ": round(D, 5), "in_PRZ": in_prz,
        "setup": "bullish_shark" if bullish else "bearish_shark",
    }
    if score < 2 or not in_prz:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    if bullish:
        return AnalyzerResult(CODE, "buy", min(85.0, 50 + score * 12), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", min(85.0, 50 + score * 12), WEIGHT_DEFAULT, payload)


class SharkPatternAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
