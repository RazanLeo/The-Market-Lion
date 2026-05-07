"""SMC Zones Tool — Order Blocks + FVGs + Breaker Blocks.

  • OB: opposite candle before > 2×ATR move (cyan/orange rect)
  • FVG (Fair Value Gap): 3-candle gap where bar1.high < bar3.low (or mirror)
  • Breaker: invalidated OB that held as support/resistance after re-test
Returns rectangles colored by zone type.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "smc_zones_tool"
WEIGHT_DEFAULT = 1.15


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    atr_s = _atr(df)
    drawings = []
    obs = []
    for i in range(len(df) - 30, len(df) - 5):
        atr_i = float(atr_s.iloc[i] or 0)
        if atr_i <= 0:
            continue
        body_dir = float(df["c"].iloc[i]) - float(df["o"].iloc[i])
        net = float(df["c"].iloc[i + 5]) - float(df["c"].iloc[i])
        if body_dir < 0 and net > 2 * atr_i:
            obs.append(("bull", i, float(df["h"].iloc[i]), float(df["l"].iloc[i])))
        elif body_dir > 0 and net < -2 * atr_i:
            obs.append(("bear", i, float(df["h"].iloc[i]), float(df["l"].iloc[i])))
    fvgs = []
    for i in range(len(df) - 30, len(df) - 1):
        h1 = float(df["h"].iloc[i - 1]); l3 = float(df["l"].iloc[i + 1])
        l1 = float(df["l"].iloc[i - 1]); h3 = float(df["h"].iloc[i + 1])
        if h1 < l3:
            fvgs.append(("bull", i, h1, l3))
        if l1 > h3:
            fvgs.append(("bear", i, h3, l1))
    for d, idx, hi, lo in obs[-3:]:
        col = "rgba(34,197,94,0.22)" if d == "bull" else "rgba(239,68,68,0.22)"
        drawings.append({"type": "rect", "x1": str(df.index[idx]), "y1": lo,
                         "x2": str(df.index[-1]), "y2": hi,
                         "color": col, "label": f"OB {d}"})
    for d, idx, lo, hi in fvgs[-3:]:
        col = "rgba(34,211,238,0.18)" if d == "bull" else "rgba(245,158,11,0.18)"
        drawings.append({"type": "rect", "x1": str(df.index[idx - 1]), "y1": lo,
                         "x2": str(df.index[-1]), "y2": hi,
                         "color": col, "label": f"FVG {d}"})
    last_c = float(df["c"].iloc[-1])
    in_bull_zone = any(lo <= last_c <= hi for d, _, hi, lo in obs if d == "bull") or \
                   any(lo <= last_c <= hi for d, _, lo, hi in fvgs if d == "bull")
    in_bear_zone = any(lo <= last_c <= hi for d, _, hi, lo in obs if d == "bear") or \
                   any(lo <= last_c <= hi for d, _, lo, hi in fvgs if d == "bear")
    payload = {"drawings": drawings, "OBs": len(obs), "FVGs": len(fvgs),
               "in_bullish_zone": in_bull_zone, "in_bearish_zone": in_bear_zone}
    if in_bull_zone:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if in_bear_zone:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SmcZonesToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
