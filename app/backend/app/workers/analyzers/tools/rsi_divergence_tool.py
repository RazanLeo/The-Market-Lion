"""RSI Divergence Tool — bullish & bearish RSI divergences.

Bullish: price makes lower-low, RSI makes higher-low.
Bearish: price makes higher-high, RSI makes lower-high.
Draws line between two price extremes + line between two RSI extremes (in payload).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "rsi_divergence_tool"
WEIGHT_DEFAULT = 1.05


def _rsi(c, n=14):
    diff = c.diff()
    up = diff.clip(lower=0); dn = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / (ad + 1e-9))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    rsi = _rsi(df["c"])
    win = df.iloc[-30:]; rsi_win = rsi.iloc[-30:]
    p_low_idx = int(win["l"].argmin()); p_high_idx = int(win["h"].argmax())
    rsi_low_idx = int(rsi_win.argmin()); rsi_high_idx = int(rsi_win.argmax())
    p_low = float(win["l"].iloc[p_low_idx]); p_high = float(win["h"].iloc[p_high_idx])
    bull_div = False; bear_div = False
    drawings = []
    # Find prior pivot
    if p_low_idx > 10:
        prev_p_low = float(win["l"].iloc[:p_low_idx - 3].min())
        prev_idx = int(win["l"].iloc[:p_low_idx - 3].argmin())
        prev_rsi = float(rsi_win.iloc[prev_idx])
        cur_rsi = float(rsi_win.iloc[p_low_idx])
        if p_low < prev_p_low and cur_rsi > prev_rsi:
            bull_div = True
            drawings.append({"type": "line", "x1": str(win.index[prev_idx]), "y1": prev_p_low,
                             "x2": str(win.index[p_low_idx]), "y2": p_low,
                             "color": "#16a34a", "label": "Bull Div Price"})
    if p_high_idx > 10:
        prev_p_high = float(win["h"].iloc[:p_high_idx - 3].max())
        prev_idx = int(win["h"].iloc[:p_high_idx - 3].argmax())
        prev_rsi = float(rsi_win.iloc[prev_idx])
        cur_rsi = float(rsi_win.iloc[p_high_idx])
        if p_high > prev_p_high and cur_rsi < prev_rsi:
            bear_div = True
            drawings.append({"type": "line", "x1": str(win.index[prev_idx]), "y1": prev_p_high,
                             "x2": str(win.index[p_high_idx]), "y2": p_high,
                             "color": "#dc2626", "label": "Bear Div Price"})
    payload = {"drawings": drawings, "bullish_divergence": bull_div,
               "bearish_divergence": bear_div, "rsi_now": round(float(rsi.iloc[-1]), 1)}
    if bull_div:
        return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if bear_div:
        return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class RsiDivergenceToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
