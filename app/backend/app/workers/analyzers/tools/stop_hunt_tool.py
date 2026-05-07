"""Stop Hunt Tool — wick spike > 1.5×ATR then close back inside.

Stop hunt = a deliberate wick that takes out resting stops, then reverses. Detects:
  bar wick (high - close) > 1.5×ATR AND close back below prior 20-bar high (bear hunt)
  bar wick (close - low) > 1.5×ATR AND close back above prior 20-bar low (bull hunt)
Draws highlight rect on the spike bar + arrow at reversal.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "stop_hunt_tool"
WEIGHT_DEFAULT = 1.05


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    atr = _atr(df)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    o = float(df["o"].iloc[-1]); c = float(df["c"].iloc[-1])
    h = float(df["h"].iloc[-1]); l = float(df["l"].iloc[-1])
    upper_wick = h - max(o, c); lower_wick = min(o, c) - l
    prev_high_20 = float(df["h"].iloc[-21:-1].max())
    prev_low_20 = float(df["l"].iloc[-21:-1].min())
    bear_hunt = upper_wick > 1.5 * atr and h > prev_high_20 and c < prev_high_20
    bull_hunt = lower_wick > 1.5 * atr and l < prev_low_20 and c > prev_low_20
    drawings = []
    ts = str(df.index[-1])
    if bear_hunt:
        drawings.append({"type": "rect", "x1": ts, "y1": prev_high_20,
                         "x2": ts, "y2": h,
                         "color": "rgba(239,68,68,0.4)", "label": "Stop Hunt ↓"})
        drawings.append({"type": "marker", "x": ts, "y": c,
                         "shape": "arrow_down", "color": "#dc2626", "label": "Reversal"})
    if bull_hunt:
        drawings.append({"type": "rect", "x1": ts, "y1": l,
                         "x2": ts, "y2": prev_low_20,
                         "color": "rgba(34,197,94,0.4)", "label": "Stop Hunt ↑"})
        drawings.append({"type": "marker", "x": ts, "y": c,
                         "shape": "arrow_up", "color": "#16a34a", "label": "Reversal"})
    payload = {"drawings": drawings,
               "upper_wick_atr": round(upper_wick / atr, 2),
               "lower_wick_atr": round(lower_wick / atr, 2),
               "bear_hunt": bear_hunt, "bull_hunt": bull_hunt}
    if bull_hunt:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if bear_hunt:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class StopHuntToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
