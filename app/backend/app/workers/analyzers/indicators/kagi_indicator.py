"""Kagi Chart — direction-only chart that ignores time, reverses on threshold.

Build Kagi line: yang (thick, up) when price exceeds prior peak; yin (thin, down) when
breaks prior trough. Reversal threshold = 4% (or 4×ATR for instruments).
Buy = yang line confirmed (latest direction = up). Sell = yin line confirmed.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "kagi_indicator"
WEIGHT_DEFAULT = 0.7


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    threshold = max(_atr(df) * 4, float(df["c"].iloc[-1]) * 0.02)
    closes = df["c"].iloc[-100:] if len(df) >= 100 else df["c"]
    line = []  # list of (price, direction) where direction in {+1 yang, -1 yin}
    cur_dir = +1 if closes.iloc[1] > closes.iloc[0] else -1
    cur_extreme = float(closes.iloc[0])
    for p in closes.iloc[1:]:
        p = float(p)
        if cur_dir == +1:
            if p > cur_extreme:
                cur_extreme = p
            elif cur_extreme - p >= threshold:
                line.append((cur_extreme, +1)); cur_dir = -1; cur_extreme = p
        else:
            if p < cur_extreme:
                cur_extreme = p
            elif p - cur_extreme >= threshold:
                line.append((cur_extreme, -1)); cur_dir = +1; cur_extreme = p
    line.append((cur_extreme, cur_dir))
    yang = sum(1 for _, d in line if d == +1)
    yin = sum(1 for _, d in line if d == -1)
    payload = {"current_direction": "yang" if cur_dir == +1 else "yin",
               "yang_segments": yang, "yin_segments": yin, "threshold": round(threshold, 5)}
    if cur_dir == +1 and yang > yin:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if cur_dir == -1 and yin > yang:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class KagiIndicatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
