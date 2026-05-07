"""MA Stack Tool — EMA20 / SMA50 / SMA200 stacking visualization.

Bull stack: EMA20 > SMA50 > SMA200 → strong uptrend.
Bear stack: EMA20 < SMA50 < SMA200 → strong downtrend.
Mixed: any other order. Shaded fills between lines colored by stack direction.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "ma_stack_tool"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 220:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    c = df["c"]
    ema20 = c.ewm(span=20, adjust=False).mean()
    sma50 = c.rolling(50).mean()
    sma200 = c.rolling(200).mean()
    e = float(ema20.iloc[-1]); s50 = float(sma50.iloc[-1]); s200 = float(sma200.iloc[-1])
    bull_stack = e > s50 > s200
    bear_stack = e < s50 < s200
    last_c = float(c.iloc[-1])
    drawings = []
    span_idx = max(0, len(df) - 100)
    drawings.append({"type": "line", "x1": str(df.index[span_idx]), "y1": float(ema20.iloc[span_idx]),
                     "x2": str(df.index[-1]), "y2": e, "color": "#C9A227", "label": "EMA20"})
    drawings.append({"type": "line", "x1": str(df.index[span_idx]), "y1": float(sma50.iloc[span_idx]),
                     "x2": str(df.index[-1]), "y2": s50, "color": "#3b82f6", "label": "SMA50"})
    drawings.append({"type": "line", "x1": str(df.index[span_idx]), "y1": float(sma200.iloc[span_idx]),
                     "x2": str(df.index[-1]), "y2": s200, "color": "#8b5cf6", "label": "SMA200"})
    fill_col = ("rgba(34,197,94,0.10)" if bull_stack else
                "rgba(239,68,68,0.10)" if bear_stack else "rgba(148,163,184,0.10)")
    drawings.append({"type": "rect", "x1": str(df.index[span_idx]),
                     "y1": min(e, s50, s200), "x2": str(df.index[-1]),
                     "y2": max(e, s50, s200), "color": fill_col, "label": "MA stack"})
    payload = {"drawings": drawings, "ema20": round(e, 5), "sma50": round(s50, 5),
               "sma200": round(s200, 5), "bull_stack": bull_stack, "bear_stack": bear_stack}
    if bull_stack and last_c > e:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if bear_stack and last_c < e:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MaStackToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
