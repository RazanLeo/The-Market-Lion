"""Liquidity Sweeps Tool — wick beyond major swing then close back inside.

Sweep up: wick high > 30-bar swing high, close < that swing high (1-3 bars window).
Sweep down: mirror. Draws horizontal line at swept level + arrow at sweep bar.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "liquidity_sweeps_tool"
WEIGHT_DEFAULT = 1.1


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 35:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-30:]
    swing_high = float(win["h"].iloc[:-3].max())
    swing_low = float(win["l"].iloc[:-3].min())
    last3 = win.iloc[-3:]
    sweep_up = bool(last3["h"].max() > swing_high and float(last3["c"].iloc[-1]) < swing_high)
    sweep_dn = bool(last3["l"].min() < swing_low and float(last3["c"].iloc[-1]) > swing_low)
    drawings = []
    if sweep_up:
        sweep_idx = int(last3["h"].argmax())
        sweep_ts = str(last3.index[sweep_idx])
        drawings.append({"type": "line", "x1": str(win.index[0]), "y1": swing_high,
                         "x2": str(df.index[-1]), "y2": swing_high,
                         "color": "#dc2626", "label": "Liquidity swept (BSL)"})
        drawings.append({"type": "marker", "x": sweep_ts, "y": float(last3["h"].iloc[sweep_idx]),
                         "shape": "arrow_down", "color": "#dc2626", "label": "Sweep↓"})
    if sweep_dn:
        sweep_idx = int(last3["l"].argmin())
        sweep_ts = str(last3.index[sweep_idx])
        drawings.append({"type": "line", "x1": str(win.index[0]), "y1": swing_low,
                         "x2": str(df.index[-1]), "y2": swing_low,
                         "color": "#16a34a", "label": "Liquidity swept (SSL)"})
        drawings.append({"type": "marker", "x": sweep_ts, "y": float(last3["l"].iloc[sweep_idx]),
                         "shape": "arrow_up", "color": "#16a34a", "label": "Sweep↑"})
    payload = {"drawings": drawings, "swing_high": swing_high, "swing_low": swing_low,
               "sweep_up": sweep_up, "sweep_down": sweep_dn}
    if sweep_dn:
        return AnalyzerResult(CODE, "buy", 78, WEIGHT_DEFAULT, payload)
    if sweep_up:
        return AnalyzerResult(CODE, "sell", 78, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LiquiditySweepsToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
