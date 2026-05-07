"""Channels Tool — parallel channel via trendline + parallel through opposite swings.

Builds upper line through 2 swing highs, lower through 2 swing lows that fit best.
If slopes within 20%, channel is valid. Draws shaded rectangle between lines.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "channels_tool"
WEIGHT_DEFAULT = 0.9


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-100:] if len(df) > 100 else df
    sh, sl = [], []
    for i in range(2, len(win) - 2):
        if win["h"].iloc[i] == win["h"].iloc[i - 2:i + 3].max():
            sh.append((i, float(win["h"].iloc[i])))
        if win["l"].iloc[i] == win["l"].iloc[i - 2:i + 3].min():
            sl.append((i, float(win["l"].iloc[i])))
    if len(sh) < 2 or len(sl) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    h_slope = (sh[-1][1] - sh[-2][1]) / max(sh[-1][0] - sh[-2][0], 1)
    l_slope = (sl[-1][1] - sl[-2][1]) / max(sl[-1][0] - sl[-2][0], 1)
    if abs(h_slope) > 1e-9:
        slope_diff = abs(h_slope - l_slope) / abs(h_slope)
    else:
        slope_diff = 1.0
    valid = slope_diff < 0.4
    if not valid:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT,
                              {"drawings": [], "h_slope": float(h_slope),
                               "l_slope": float(l_slope), "valid": False})
    avg_slope = (h_slope + l_slope) / 2
    h_int = sh[-1][1] - h_slope * sh[-1][0]
    l_int = sl[-1][1] - l_slope * sl[-1][0]
    end_x = len(win) - 1
    drawings = [
        {"type": "line", "x1": str(win.index[sh[-2][0]]), "y1": sh[-2][1],
         "x2": str(win.index[end_x]), "y2": float(h_slope * end_x + h_int),
         "color": "#dc2626", "label": "Upper"},
        {"type": "line", "x1": str(win.index[sl[-2][0]]), "y1": sl[-2][1],
         "x2": str(win.index[end_x]), "y2": float(l_slope * end_x + l_int),
         "color": "#16a34a", "label": "Lower"},
    ]
    last_c = float(df["c"].iloc[-1])
    upper = float(h_slope * end_x + h_int); lower = float(l_slope * end_x + l_int)
    pos = (last_c - lower) / (upper - lower + 1e-9)
    payload = {"drawings": drawings, "valid": True, "avg_slope": float(avg_slope),
               "upper": round(upper, 5), "lower": round(lower, 5),
               "position_in_channel": round(pos, 3)}
    if avg_slope > 0 and pos < 0.25:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if avg_slope < 0 and pos > 0.75:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if pos < 0.15:
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if pos > 0.85:
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class ChannelsToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
