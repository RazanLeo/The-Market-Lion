"""Quasimodo (QM) Reversal — over-and-under structure shift.

Bearish QM: HH followed by LL followed by HH (3 swings) where the second HH fails;
specifically: an existing uptrend forms HH(1) → HL(2) → HH(3) → break of the HL → LH(5) at or near HH(3).
Implementation:
  • Take last 5 alternating swings.
  • Bearish: H1, L1, H2, L2, H3   with H2>H1, L2<L1, H3 near H2.
  • Bullish (mirror): L1, H1, L2, H2, L3 with L2<L1, H2>H1, L3 near L2.
QM line = the broken swing (HL for bear, LH for bull). Strong reversal at retest of QM line.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "quasimodo_qm"
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
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 4)
    if len(pivs) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last5 = pivs[-5:]
    types = "".join(p[1] for p in last5)

    bearish_qm = bullish_qm = False
    qm_line = None
    if types == "HLHLH":
        H1, L1, H2, L2, H3 = (p[2] for p in last5)
        if H2 > H1 and L2 < L1 and abs(H3 - H2) / H2 < 0.005:
            bearish_qm = True
            qm_line = L1
    if types == "LHLHL":
        L1, H1, L2, H2, L3 = (p[2] for p in last5)
        if L2 < L1 and H2 > H1 and abs(L3 - L2) / L2 < 0.005:
            bullish_qm = True
            qm_line = H1

    if not (bearish_qm or bullish_qm):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})

    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    last_close = float(df["c"].iloc[-1])
    near_qm = abs(last_close - qm_line) < atr * 0.5

    payload = {"types": types, "QM_line": round(qm_line, 5),
               "setup": "bearish_QM" if bearish_qm else "bullish_QM",
               "near_QM_line": near_qm}
    if not near_qm:
        return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)
    if bearish_qm:
        return AnalyzerResult(CODE, "sell", 80.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "buy", 80.0, WEIGHT_DEFAULT, payload)


class QuasimodoQmAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
