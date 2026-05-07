"""Order Block Tool — ICT order blocks (last opposite candle before > 2×ATR move).

Bullish OB: last bearish candle before a > 2×ATR rally (within 5 bars).
Bearish OB: last bullish candle before a > 2×ATR drop.
Draws rectangle from candle high to low; shaded by direction.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "order_block_tool"
WEIGHT_DEFAULT = 1.15


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    atr_series = _atr(df)
    blocks = []  # list of (idx, direction, high, low)
    for i in range(len(df) - 30, len(df) - 5):
        if pd.isna(atr_series.iloc[i]) or atr_series.iloc[i] <= 0:
            continue
        atr_i = float(atr_series.iloc[i])
        bar_dir = float(df["c"].iloc[i]) - float(df["o"].iloc[i])
        # next 5 bars net move
        net = float(df["c"].iloc[i + 5]) - float(df["c"].iloc[i])
        if bar_dir < 0 and net > 2 * atr_i:  # bullish OB
            blocks.append({"idx": i, "dir": "bull",
                           "high": float(df["h"].iloc[i]), "low": float(df["l"].iloc[i])})
        elif bar_dir > 0 and net < -2 * atr_i:  # bearish OB
            blocks.append({"idx": i, "dir": "bear",
                           "high": float(df["h"].iloc[i]), "low": float(df["l"].iloc[i])})
    last_c = float(df["c"].iloc[-1])
    drawings = []
    for b in blocks[-5:]:
        ts = str(df.index[b["idx"]])
        color = "rgba(34,197,94,0.22)" if b["dir"] == "bull" else "rgba(239,68,68,0.22)"
        drawings.append({"type": "rect", "x1": ts, "y1": b["low"],
                         "x2": str(df.index[-1]), "y2": b["high"],
                         "color": color, "label": f"OB {b['dir']}"})
    bull_obs = [b for b in blocks if b["dir"] == "bull" and b["low"] <= last_c <= b["high"]]
    bear_obs = [b for b in blocks if b["dir"] == "bear" and b["low"] <= last_c <= b["high"]]
    payload = {"drawings": drawings, "blocks_count": len(blocks),
               "bull_OBs": len([b for b in blocks if b["dir"] == "bull"]),
               "bear_OBs": len([b for b in blocks if b["dir"] == "bear"]),
               "in_bullish_OB": len(bull_obs) > 0,
               "in_bearish_OB": len(bear_obs) > 0}
    if bull_obs:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if bear_obs:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class OrderBlockToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
