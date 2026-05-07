"""ARC Breakout Tool — horizontal line at swing extreme + shaded post-breakout zone.

Detects breakouts: close beyond 20-bar swing high/low + volume > 1.5× avg.
Strength = breakout_size / ATR. Draws horizontal level line + rectangle of post-break.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "arc_breakout_tool"
WEIGHT_DEFAULT = 1.05


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    atr = _atr(df)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    swing_high = float(df["h"].iloc[-21:-1].max())
    swing_low = float(df["l"].iloc[-21:-1].min())
    last_c = float(df["c"].iloc[-1])
    vol_avg = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    vol_ok = float(df["v"].iloc[-1]) > 1.5 * vol_avg if vol_avg > 0 else False
    bull_break = last_c > swing_high and vol_ok
    bear_break = last_c < swing_low and vol_ok
    drawings = []
    if bull_break:
        size = (last_c - swing_high) / atr
        drawings.append({"type": "line", "x1": str(df.index[-21]), "y1": swing_high,
                         "x2": str(df.index[-1]), "y2": swing_high,
                         "color": "#C9A227", "label": "ARC up"})
        drawings.append({"type": "rect", "x1": str(df.index[-1]), "y1": swing_high,
                         "x2": str(df.index[-1]), "y2": last_c,
                         "color": "rgba(34,197,94,0.18)", "label": "ARC zone"})
        drawings.append({"type": "marker", "x": str(df.index[-1]), "y": last_c,
                         "shape": "arrow_up", "color": "#16a34a", "label": "ARC↑"})
        return AnalyzerResult(CODE, "buy", min(85, 55 + size * 8), WEIGHT_DEFAULT,
                              {"drawings": drawings, "atr": round(atr, 5),
                               "swing_high": swing_high, "size_atr": round(size, 2)})
    if bear_break:
        size = (swing_low - last_c) / atr
        drawings.append({"type": "line", "x1": str(df.index[-21]), "y1": swing_low,
                         "x2": str(df.index[-1]), "y2": swing_low,
                         "color": "#C9A227", "label": "ARC dn"})
        drawings.append({"type": "rect", "x1": str(df.index[-1]), "y1": last_c,
                         "x2": str(df.index[-1]), "y2": swing_low,
                         "color": "rgba(239,68,68,0.18)", "label": "ARC zone"})
        drawings.append({"type": "marker", "x": str(df.index[-1]), "y": last_c,
                         "shape": "arrow_down", "color": "#dc2626", "label": "ARC↓"})
        return AnalyzerResult(CODE, "sell", min(85, 55 + size * 8), WEIGHT_DEFAULT,
                              {"drawings": drawings, "atr": round(atr, 5),
                               "swing_low": swing_low, "size_atr": round(size, 2)})
    drawings.append({"type": "line", "x1": str(df.index[-21]), "y1": swing_high,
                     "x2": str(df.index[-1]), "y2": swing_high,
                     "color": "rgba(201,162,39,0.5)", "label": "Pending high"})
    drawings.append({"type": "line", "x1": str(df.index[-21]), "y1": swing_low,
                     "x2": str(df.index[-1]), "y2": swing_low,
                     "color": "rgba(201,162,39,0.5)", "label": "Pending low"})
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT,
                          {"drawings": drawings, "swing_high": swing_high, "swing_low": swing_low})


class ArcBreakoutToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
