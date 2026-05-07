"""Trend Lines Tool — auto trendlines via linear regression over swing pivots.

Fit regression line over last 3 swing lows (uptrend) and 3 swing highs (downtrend).
Slope sign decides primary trend. Extends the line forward by 10 bars.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "trend_lines_tool"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-100:] if len(df) > 100 else df
    swing_lows, swing_highs = [], []
    for i in range(2, len(win) - 2):
        if win["l"].iloc[i] == win["l"].iloc[i - 2:i + 3].min():
            swing_lows.append((i, float(win["l"].iloc[i])))
        if win["h"].iloc[i] == win["h"].iloc[i - 2:i + 3].max():
            swing_highs.append((i, float(win["h"].iloc[i])))
    drawings = []
    bull_slope = bear_slope = 0
    if len(swing_lows) >= 3:
        last3 = swing_lows[-3:]
        x = np.array([p[0] for p in last3], dtype=float)
        y = np.array([p[1] for p in last3], dtype=float)
        bull_slope, bull_int = np.polyfit(x, y, 1)
        x_start, x_end = last3[0][0], min(len(win) + 10, len(win) - 1 + 10)
        idx_end = min(len(df) - 1, len(df) - len(win) + len(win) - 1 + 10)
        idx_end = min(idx_end, len(df) - 1)
        drawings.append({"type": "line",
                         "x1": str(win.index[x_start]), "y1": float(bull_slope * x_start + bull_int),
                         "x2": str(df.index[idx_end]), "y2": float(bull_slope * (len(win) - 1) + bull_int),
                         "color": "#16a34a", "label": f"Trend↑ slope={bull_slope:.5f}"})
    if len(swing_highs) >= 3:
        last3h = swing_highs[-3:]
        xh = np.array([p[0] for p in last3h], dtype=float)
        yh = np.array([p[1] for p in last3h], dtype=float)
        bear_slope, bear_int = np.polyfit(xh, yh, 1)
        x_start_h = last3h[0][0]
        idx_end_h = min(len(df) - 1, len(df) - len(win) + len(win) - 1 + 10)
        idx_end_h = min(idx_end_h, len(df) - 1)
        drawings.append({"type": "line",
                         "x1": str(win.index[x_start_h]), "y1": float(bear_slope * x_start_h + bear_int),
                         "x2": str(df.index[idx_end_h]), "y2": float(bear_slope * (len(win) - 1) + bear_int),
                         "color": "#dc2626", "label": f"Trend↓ slope={bear_slope:.5f}"})
    payload = {"drawings": drawings,
               "bull_trend_slope": float(bull_slope) if isinstance(bull_slope, np.floating) else bull_slope,
               "bear_trend_slope": float(bear_slope) if isinstance(bear_slope, np.floating) else bear_slope,
               "swing_lows": len(swing_lows), "swing_highs": len(swing_highs)}
    if bull_slope > 0 and abs(bull_slope) > abs(bear_slope):
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if bear_slope < 0 and abs(bear_slope) > abs(bull_slope):
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class TrendLinesToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
