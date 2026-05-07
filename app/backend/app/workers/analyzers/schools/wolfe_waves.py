"""Wolfe Waves — 5-point reversal pattern with EPA target line and ETA timing.

Bearish setup (Sell Wolfe):
  point-1 = swing low,  point-2 = swing high (P2 > P1).
  point-3 = swing low > P1 ; point-4 = swing high < P2 ; point-5 = swing low < P3.
  EPA line = trendline drawn through P1 & P4.
  Target = intersection of EPA with P5's vertical.

Bullish setup is the mirror image.

ETA = bars expected from P5 until target hit, derived from slope of P1-P4 line × distance.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "wolfe_waves"
WEIGHT_DEFAULT = 1.0


def _swings(df: pd.DataFrame, n: int = 4):
    pivots = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivots.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivots.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivots)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 4)
    if len(pivs) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last5 = pivs[-5:]
    types = "".join(p[1] for p in last5)
    P = [(p[0], p[2]) for p in last5]
    bullish = bearish = False
    # Bearish Wolfe: L H L H L  with P3>P1, P4<P2, P5<P3
    if types == "LHLHL":
        if P[2][1] > P[0][1] and P[3][1] < P[1][1] and P[4][1] < P[2][1]:
            bearish = True
    # Bullish Wolfe: H L H L H with P3<P1, P4>P2, P5>P3
    if types == "HLHLH":
        if P[2][1] < P[0][1] and P[3][1] > P[1][1] and P[4][1] > P[2][1]:
            bullish = True

    if not (bullish or bearish):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})

    p1, p4 = P[0], P[3]
    if p4[0] - p1[0] == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    slope = (p4[1] - p1[1]) / (p4[0] - p1[0])
    last_t = len(df) - 1
    target = p1[1] + slope * (last_t - p1[0])
    last_close = float(df["c"].iloc[-1])
    eta_bars = int(abs((target - last_close) / max(abs(slope), 1e-9))) if slope != 0 else 0

    payload = {
        "type": "bearish_wolfe" if bearish else "bullish_wolfe",
        "P1": [p1[0], round(p1[1], 5)],
        "P2": [P[1][0], round(P[1][1], 5)],
        "P3": [P[2][0], round(P[2][1], 5)],
        "P4": [p4[0], round(p4[1], 5)],
        "P5": [P[4][0], round(P[4][1], 5)],
        "epa_slope_per_bar": round(float(slope), 6),
        "epa_target_now": round(float(target), 5),
        "eta_bars_from_now": eta_bars,
    }
    if bullish:
        return AnalyzerResult(CODE, "buy", 75.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 75.0, WEIGHT_DEFAULT, payload)


class WolfeWavesAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
