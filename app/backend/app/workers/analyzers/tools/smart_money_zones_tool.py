"""Smart Money Zones — Premium / Discount / Equilibrium (ICT).

Computes 80-bar swing range:
  EQ (50%) = midpoint of (high - low)
  Discount = below EQ (best buy zone)
  Premium  = above EQ (best sell zone)
Draws shaded rectangles for each zone + horizontal EQ line.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "smart_money_zones_tool"
WEIGHT_DEFAULT = 1.05


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-80:] if len(df) > 80 else df
    hi = float(win["h"].max()); lo = float(win["l"].min())
    if hi <= lo:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    eq = (hi + lo) / 2
    last_c = float(df["c"].iloc[-1])
    rng = hi - lo
    pct = (last_c - lo) / rng
    drawings = [
        {"type": "rect", "x1": str(win.index[0]), "y1": lo,
         "x2": str(df.index[-1]), "y2": eq,
         "color": "rgba(34,197,94,0.10)", "label": "Discount"},
        {"type": "rect", "x1": str(win.index[0]), "y1": eq,
         "x2": str(df.index[-1]), "y2": hi,
         "color": "rgba(239,68,68,0.10)", "label": "Premium"},
        {"type": "line", "x1": str(win.index[0]), "y1": eq,
         "x2": str(df.index[-1]), "y2": eq,
         "color": "#C9A227", "label": "EQ 50%"},
    ]
    zone = "Discount" if pct < 0.4 else "Premium" if pct > 0.6 else "Equilibrium"
    payload = {"drawings": drawings, "high": round(hi, 5), "low": round(lo, 5),
               "EQ": round(eq, 5), "pct_in_range": round(pct, 3), "zone": zone}
    if zone == "Discount" and last_c > float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if zone == "Premium" and last_c < float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SmartMoneyZonesToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
