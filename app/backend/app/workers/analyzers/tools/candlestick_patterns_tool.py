"""Candlestick Patterns Tool — detect & mark Doji / Hammer / Engulfing.

  • Doji: |c-o| < 0.1 × range
  • Hammer: lower wick > 2× body AND upper wick < 0.5× body, near swing low
  • Inverted Hammer: upper wick > 2× body AND lower wick < 0.5× body, near swing low
  • Bullish/Bearish Engulfing
Adds markers at detected bars.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "candlestick_patterns_tool"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    o, h, l, c = df["o"], df["h"], df["l"], df["c"]
    drawings = []
    found = {"doji": 0, "hammer": 0, "inv_hammer": 0, "bull_engulf": 0, "bear_engulf": 0}
    swing_low = float(l.iloc[-20:].min())
    swing_high = float(h.iloc[-20:].max())
    for i in range(max(1, len(df) - 15), len(df)):
        body = abs(float(c.iloc[i]) - float(o.iloc[i]))
        rng = float(h.iloc[i] - l.iloc[i])
        if rng <= 0: continue
        upper = float(h.iloc[i]) - max(float(o.iloc[i]), float(c.iloc[i]))
        lower = min(float(o.iloc[i]), float(c.iloc[i])) - float(l.iloc[i])
        ts = str(df.index[i])
        is_doji = body < 0.1 * rng
        is_hammer = lower > 2 * body and upper < 0.5 * body and abs(float(l.iloc[i]) - swing_low) < rng
        is_inv_h = upper > 2 * body and lower < 0.5 * body and abs(float(l.iloc[i]) - swing_low) < rng
        is_bull_eng = (i > 0 and float(c.iloc[i]) > float(o.iloc[i - 1]) and
                       float(o.iloc[i]) < float(c.iloc[i - 1]) and float(c.iloc[i - 1]) < float(o.iloc[i - 1]))
        is_bear_eng = (i > 0 and float(c.iloc[i]) < float(o.iloc[i - 1]) and
                       float(o.iloc[i]) > float(c.iloc[i - 1]) and float(c.iloc[i - 1]) > float(o.iloc[i - 1]))
        if is_doji:
            drawings.append({"type": "marker", "x": ts, "y": float(c.iloc[i]),
                             "shape": "circle", "color": "#94a3b8", "label": "Doji"}); found["doji"] += 1
        if is_hammer:
            drawings.append({"type": "marker", "x": ts, "y": float(l.iloc[i]),
                             "shape": "triangle_up", "color": "#16a34a", "label": "Hammer"}); found["hammer"] += 1
        if is_inv_h:
            drawings.append({"type": "marker", "x": ts, "y": float(h.iloc[i]),
                             "shape": "triangle_up", "color": "#16a34a", "label": "Inv Hammer"}); found["inv_hammer"] += 1
        if is_bull_eng:
            drawings.append({"type": "marker", "x": ts, "y": float(l.iloc[i]),
                             "shape": "arrow_up", "color": "#16a34a", "label": "Bull Engulf"}); found["bull_engulf"] += 1
        if is_bear_eng:
            drawings.append({"type": "marker", "x": ts, "y": float(h.iloc[i]),
                             "shape": "arrow_down", "color": "#dc2626", "label": "Bear Engulf"}); found["bear_engulf"] += 1
    payload = {"drawings": drawings, "patterns_found": found}
    last_idx = len(df) - 1
    last_o = float(o.iloc[last_idx]); last_c = float(c.iloc[last_idx])
    last_body = abs(last_c - last_o); last_rng = float(h.iloc[last_idx] - l.iloc[last_idx])
    last_lower = min(last_o, last_c) - float(l.iloc[last_idx])
    last_upper = float(h.iloc[last_idx]) - max(last_o, last_c)
    if last_rng > 0:
        if last_lower > 2 * last_body and abs(float(l.iloc[last_idx]) - swing_low) < last_rng:
            return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
        if last_upper > 2 * last_body and abs(float(h.iloc[last_idx]) - swing_high) < last_rng:
            return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if found["bull_engulf"] >= 1:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if found["bear_engulf"] >= 1:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CandlestickPatternsToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
