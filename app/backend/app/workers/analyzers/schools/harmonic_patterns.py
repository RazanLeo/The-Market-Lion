"""Harmonic Patterns — Gartley, Bat, Butterfly, Crab.

Each is built from 5 pivots X-A-B-C-D with strict Fibonacci ratio rules:

  Gartley:
    AB = 0.618 of XA      (tol 0.55–0.65)
    BC = 0.382–0.886 of AB
    CD = 1.13–1.618 of BC
    AD = 0.786 of XA      (tol 0.75–0.82)

  Bat:
    AB = 0.382–0.5 of XA
    BC = 0.382–0.886 of AB
    CD = 1.618–2.618 of BC
    AD = 0.886 of XA      (tol 0.85–0.92)

  Butterfly:
    AB = 0.786 of XA      (tol 0.75–0.82)
    BC = 0.382–0.886 of AB
    CD = 1.618–2.618 of BC
    AD = 1.27–1.618 of XA

  Crab:
    AB = 0.382–0.618 of XA
    BC = 0.382–0.886 of AB
    CD = 2.618–3.618 of BC
    AD = 1.618 of XA      (tol 1.55–1.68)

PRZ (Potential Reversal Zone) = D ± 0.3×ATR.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "harmonic_patterns"
WEIGHT_DEFAULT = 1.05


def _swings(df: pd.DataFrame, n: int = 5):
    pivots = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivots.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivots.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivots)


def _between(x: float, lo: float, hi: float) -> bool:
    return lo <= x <= hi


def _check(name: str, X: float, A: float, B: float, C: float, D: float, bullish: bool) -> dict | None:
    XA = abs(A - X); AB = abs(B - A); BC = abs(C - B); CD = abs(D - C); AD = abs(D - A)
    if XA == 0 or AB == 0 or BC == 0:
        return None
    ab_xa = AB / XA; bc_ab = BC / AB; cd_bc = CD / BC; ad_xa = AD / XA

    rules = {
        "Gartley":   ((0.55, 0.65), (0.382, 0.886), (1.13, 1.618), (0.75, 0.82)),
        "Bat":       ((0.382, 0.5), (0.382, 0.886), (1.618, 2.618), (0.85, 0.92)),
        "Butterfly": ((0.75, 0.82), (0.382, 0.886), (1.618, 2.618), (1.27, 1.618)),
        "Crab":      ((0.382, 0.618), (0.382, 0.886), (2.618, 3.618), (1.55, 1.68)),
    }
    if name not in rules: return None
    r = rules[name]
    ok_ab = _between(ab_xa, *r[0])
    ok_bc = _between(bc_ab, *r[1])
    ok_cd = _between(cd_bc, *r[2])
    ok_ad = _between(ad_xa, *r[3])
    score = sum([ok_ab, ok_bc, ok_cd, ok_ad])
    if score < 3:
        return None
    return {"name": name, "score": score, "ratios": {
        "AB/XA": round(ab_xa, 3), "BC/AB": round(bc_ab, 3),
        "CD/BC": round(cd_bc, 3), "AD/XA": round(ad_xa, 3),
    }}


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 5)
    if len(pivs) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"pivots": len(pivs)})
    last5 = pivs[-5:]
    types = "".join(p[1] for p in last5)
    bullish_xabcd = types in ("LHLHL", "LHLLH")
    bearish_xabcd = types in ("HLHLH", "HLHHL")
    if not (bullish_xabcd or bearish_xabcd):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})

    X, A, B, C, D = (p[2] for p in last5)
    bullish = bullish_xabcd

    detected = []
    for name in ("Gartley", "Bat", "Butterfly", "Crab"):
        d = _check(name, X, A, B, C, D, bullish)
        if d: detected.append(d)

    if not detected:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})

    best = max(detected, key=lambda x: x["score"])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    prz_low = D - atr * 0.3; prz_high = D + atr * 0.3
    last_close = float(df["c"].iloc[-1])
    in_prz = prz_low <= last_close <= prz_high

    payload = {
        "pattern": best["name"], "rules_passed": best["score"], "ratios": best["ratios"],
        "bullish_setup": bullish, "X": round(X, 5), "A": round(A, 5),
        "B": round(B, 5), "C": round(C, 5), "D": round(D, 5),
        "PRZ": [round(prz_low, 5), round(prz_high, 5)],
        "in_PRZ": in_prz, "all_detected": [d["name"] for d in detected],
    }

    if not in_prz:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)

    base = 50 + best["score"] * 8
    if bullish:
        return AnalyzerResult(CODE, "buy", min(90.0, base), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", min(90.0, base), WEIGHT_DEFAULT, payload)


class HarmonicPatternsAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
