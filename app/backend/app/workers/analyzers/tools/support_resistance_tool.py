"""Support/Resistance Tool — auto S/R from pivot clusters.

Detects 2-bar swing pivots in last 200 bars, clusters them by tolerance 0.5×ATR,
keeps top-3 supports below price + top-3 resistances above. Line thickness in payload
= touches count.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "support_resistance_tool"
WEIGHT_DEFAULT = 1.1


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def _cluster(values, tol):
    if not values: return []
    values = sorted(values)
    out = [[values[0]]]
    for v in values[1:]:
        if v - out[-1][-1] <= tol:
            out[-1].append(v)
        else:
            out.append([v])
    return [(sum(g) / len(g), len(g)) for g in out]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    atr = _atr(df)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-200:] if len(df) > 200 else df
    highs, lows = [], []
    for i in range(2, len(win) - 2):
        if win["h"].iloc[i] == win["h"].iloc[i - 2:i + 3].max():
            highs.append(float(win["h"].iloc[i]))
        if win["l"].iloc[i] == win["l"].iloc[i - 2:i + 3].min():
            lows.append(float(win["l"].iloc[i]))
    res = sorted(_cluster(highs, atr * 0.5), key=lambda x: -x[1])[:3]
    sup = sorted(_cluster(lows, atr * 0.5), key=lambda x: -x[1])[:3]
    drawings = []
    last_c = float(df["c"].iloc[-1])
    for p, n in res:
        drawings.append({"type": "line", "x1": str(win.index[0]), "y1": p,
                         "x2": str(df.index[-1]), "y2": p,
                         "color": "#dc2626", "thickness": min(4, n),
                         "label": f"R×{n}"})
    for p, n in sup:
        drawings.append({"type": "line", "x1": str(win.index[0]), "y1": p,
                         "x2": str(df.index[-1]), "y2": p,
                         "color": "#16a34a", "thickness": min(4, n),
                         "label": f"S×{n}"})
    nearest_sup = max([s for s in sup if s[0] <= last_c], key=lambda x: x[0], default=None)
    nearest_res = min([r for r in res if r[0] >= last_c], key=lambda x: x[0], default=None)
    payload = {"drawings": drawings, "supports": sup, "resistances": res,
               "nearest_support": nearest_sup, "nearest_resistance": nearest_res}
    if nearest_sup and abs(last_c - nearest_sup[0]) < atr * 0.3 and nearest_sup[1] >= 2:
        return AnalyzerResult(CODE, "buy", min(80, 50 + nearest_sup[1] * 8), WEIGHT_DEFAULT, payload)
    if nearest_res and abs(last_c - nearest_res[0]) < atr * 0.3 and nearest_res[1] >= 2:
        return AnalyzerResult(CODE, "sell", min(80, 50 + nearest_res[1] * 8), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SupportResistanceToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
