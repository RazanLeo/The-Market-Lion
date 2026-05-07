"""Pivot HL Tool — recent swing highs/lows as markers + connecting line.

Draws dots at all 5-bar swing pivots in last 60 bars, with a polyline through them.
Useful for visual structure analysis (HH/HL/LH/LL).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "pivot_hl_tool"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-60:] if len(df) > 60 else df
    pivs = []  # (idx, price, type)
    for i in range(2, len(win) - 2):
        if win["h"].iloc[i] == win["h"].iloc[i - 2:i + 3].max():
            pivs.append((i, float(win["h"].iloc[i]), "H"))
        if win["l"].iloc[i] == win["l"].iloc[i - 2:i + 3].min():
            pivs.append((i, float(win["l"].iloc[i]), "L"))
    pivs.sort()
    drawings = []
    for idx, p, t in pivs:
        col = "#dc2626" if t == "H" else "#16a34a"
        drawings.append({"type": "marker", "x": str(win.index[idx]), "y": p,
                         "shape": "circle", "color": col, "label": t})
    for i in range(1, len(pivs)):
        prev_i, prev_p, _ = pivs[i - 1]
        cur_i, cur_p, _ = pivs[i]
        drawings.append({"type": "line", "x1": str(win.index[prev_i]), "y1": prev_p,
                         "x2": str(win.index[cur_i]), "y2": cur_p,
                         "color": "rgba(201,162,39,0.6)", "label": ""})
    # Determine HH/HL/LH/LL trend based on last 4 pivots
    highs = [p for p in pivs if p[2] == "H"][-2:]
    lows = [p for p in pivs if p[2] == "L"][-2:]
    bull = (len(highs) == 2 and len(lows) == 2 and
            highs[1][1] > highs[0][1] and lows[1][1] > lows[0][1])
    bear = (len(highs) == 2 and len(lows) == 2 and
            highs[1][1] < highs[0][1] and lows[1][1] < lows[0][1])
    payload = {"drawings": drawings, "pivots_count": len(pivs),
               "structure": "HH/HL" if bull else "LH/LL" if bear else "mixed"}
    if bull:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if bear:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class PivotHlToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
