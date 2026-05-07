"""Fib Extension Tool — projection levels for breakout targets.

After breaking 80-bar swing high (or low), projects 1.272 / 1.618 / 2.618 extensions
based on the prior leg height. Used to set TP1/TP2/TP3 after entry.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fib_extension_tool"
WEIGHT_DEFAULT = 0.85
EXT = [1.272, 1.618, 2.618]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-80:]
    hi = float(win["h"].max()); lo = float(win["l"].min())
    leg = hi - lo
    last_c = float(df["c"].iloc[-1])
    drawings = []
    if last_c > hi * 1.001:  # broken upward → upward extensions
        for lv in EXT:
            p = hi + leg * (lv - 1)
            drawings.append({"type": "line", "x1": str(win.index[0]), "y1": p,
                             "x2": str(df.index[-1]), "y2": p,
                             "color": "rgba(34,197,94,0.7)", "label": f"TP {lv:.3f} = {p:.5f}"})
        targets = [round(hi + leg * (lv - 1), 5) for lv in EXT]
        payload = {"drawings": drawings, "direction": "up", "leg": round(leg, 5), "targets": targets}
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last_c < lo * 0.999:
        for lv in EXT:
            p = lo - leg * (lv - 1)
            drawings.append({"type": "line", "x1": str(win.index[0]), "y1": p,
                             "x2": str(df.index[-1]), "y2": p,
                             "color": "rgba(239,68,68,0.7)", "label": f"TP {lv:.3f} = {p:.5f}"})
        targets = [round(lo - leg * (lv - 1), 5) for lv in EXT]
        payload = {"drawings": drawings, "direction": "down", "leg": round(leg, 5), "targets": targets}
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    payload = {"drawings": [], "leg": round(leg, 5), "high": hi, "low": lo, "direction": "no_breakout"}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FibExtensionToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
