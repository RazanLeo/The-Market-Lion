"""Price Patterns Tool — Head & Shoulders / Double Top / Triangle detection.

Scans last 100 bars for swing pivots and matches:
  • H&S: 3 swing highs where mid > sides AND sides ~ equal (within tol)
  • Double Top / Bottom: 2 nearby same-level extremes
  • Triangle: converging trend lines
Draws connecting lines between pivots.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "price_patterns_tool"
WEIGHT_DEFAULT = 1.0


def _pivots(df, n=3):
    highs, lows = [], []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            highs.append((i, float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            lows.append((i, float(df["l"].iloc[i])))
    return highs, lows


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-100:] if len(df) > 100 else df
    highs, lows = _pivots(win, 3)
    drawings = []; patterns_found = []
    # H&S: take last 3 highs
    if len(highs) >= 3:
        a, b, c = highs[-3], highs[-2], highs[-1]
        if b[1] > a[1] and b[1] > c[1] and abs(a[1] - c[1]) / b[1] < 0.03:
            patterns_found.append("H&S")
            for p1, p2 in [(a, b), (b, c)]:
                drawings.append({"type": "line", "x1": str(win.index[p1[0]]), "y1": p1[1],
                                 "x2": str(win.index[p2[0]]), "y2": p2[1],
                                 "color": "#dc2626", "label": "H&S"})
    if len(lows) >= 3:
        a, b, c = lows[-3], lows[-2], lows[-1]
        if b[1] < a[1] and b[1] < c[1] and abs(a[1] - c[1]) / b[1] < 0.03:
            patterns_found.append("Inv H&S")
            for p1, p2 in [(a, b), (b, c)]:
                drawings.append({"type": "line", "x1": str(win.index[p1[0]]), "y1": p1[1],
                                 "x2": str(win.index[p2[0]]), "y2": p2[1],
                                 "color": "#16a34a", "label": "Inv H&S"})
    # Double top
    if len(highs) >= 2 and abs(highs[-1][1] - highs[-2][1]) / highs[-1][1] < 0.01:
        patterns_found.append("Double Top")
        drawings.append({"type": "line", "x1": str(win.index[highs[-2][0]]), "y1": highs[-2][1],
                         "x2": str(win.index[highs[-1][0]]), "y2": highs[-1][1],
                         "color": "#dc2626", "label": "Double Top"})
    if len(lows) >= 2 and abs(lows[-1][1] - lows[-2][1]) / lows[-1][1] < 0.01:
        patterns_found.append("Double Bottom")
        drawings.append({"type": "line", "x1": str(win.index[lows[-2][0]]), "y1": lows[-2][1],
                         "x2": str(win.index[lows[-1][0]]), "y2": lows[-1][1],
                         "color": "#16a34a", "label": "Double Bottom"})
    # Triangle: highs descending + lows ascending (symmetric)
    if len(highs) >= 2 and len(lows) >= 2:
        descending_h = highs[-1][1] < highs[-2][1]
        ascending_l = lows[-1][1] > lows[-2][1]
        if descending_h and ascending_l:
            patterns_found.append("Sym Triangle")
            drawings.append({"type": "line", "x1": str(win.index[highs[-2][0]]), "y1": highs[-2][1],
                             "x2": str(win.index[highs[-1][0]]), "y2": highs[-1][1],
                             "color": "#C9A227", "label": "Triangle ↓"})
            drawings.append({"type": "line", "x1": str(win.index[lows[-2][0]]), "y1": lows[-2][1],
                             "x2": str(win.index[lows[-1][0]]), "y2": lows[-1][1],
                             "color": "#C9A227", "label": "Triangle ↑"})
    payload = {"drawings": drawings, "patterns_found": patterns_found}
    if "Inv H&S" in patterns_found or "Double Bottom" in patterns_found:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if "H&S" in patterns_found or "Double Top" in patterns_found:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class PricePatternsToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
