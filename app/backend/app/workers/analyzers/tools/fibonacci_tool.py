"""Fibonacci Tool — auto-applied retracement levels on last leg.

Detects high/low of last 80 bars, draws 0.236/0.382/0.5/0.618/0.786 retracement levels
+ extension levels 1.272 / 1.618 / 2.618. Returns buy at 0.618 if price is rebounding.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci_tool"
WEIGHT_DEFAULT = 1.0
RET_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
EXT_LEVELS = [1.272, 1.618, 2.618]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    win = df.iloc[-80:]
    hi_i = int(win["h"].argmax()); lo_i = int(win["l"].argmin())
    hi = float(win["h"].iloc[hi_i]); lo = float(win["l"].iloc[lo_i])
    if hi <= lo:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    bullish = lo_i < hi_i
    drawings = []
    for lv in RET_LEVELS:
        p = hi - (hi - lo) * lv if bullish else lo + (hi - lo) * lv
        drawings.append({"type": "line", "x1": str(win.index[min(lo_i, hi_i)]), "y1": p,
                         "x2": str(df.index[-1]), "y2": p,
                         "color": "#C9A227", "label": f"Fib {lv:.3f}"})
    for lv in EXT_LEVELS:
        p = hi + (hi - lo) * (lv - 1) if bullish else lo - (hi - lo) * (lv - 1)
        drawings.append({"type": "line", "x1": str(win.index[max(lo_i, hi_i)]), "y1": p,
                         "x2": str(df.index[-1]), "y2": p,
                         "color": "rgba(201,162,39,0.5)", "label": f"Ext {lv:.3f}"})
    last_c = float(df["c"].iloc[-1])
    pct = (last_c - lo) / (hi - lo)
    target_618 = (1 - 0.618) if bullish else 0.618
    on_618 = abs(pct - target_618) < 0.025
    payload = {"drawings": drawings, "high": hi, "low": lo,
               "leg": "up" if bullish else "down",
               "pct_in_leg": round(pct, 3), "on_0.618": on_618}
    if bullish and on_618 and last_c > float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if (not bullish) and on_618 and last_c < float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FibonacciToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
