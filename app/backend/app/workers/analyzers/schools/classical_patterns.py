"""Classical Patterns — Edwards & Magee classical chart patterns.

Detects: Flag (sharp move + tight consolidation 5-15 bars), Pennant (converging triangle
after move), Cup-and-Handle (rounded bottom + small pullback). Returns directional bias
based on prior trend direction (continuation patterns).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "classical_patterns"
WEIGHT_DEFAULT = 0.95


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_30 = df.iloc[-30:]
    flag_pole = df.iloc[-30:-12]
    pole_move = float(flag_pole["c"].iloc[-1]) - float(flag_pole["c"].iloc[0])
    pole_strong = abs(pole_move) > 5 * atr
    consol = df.iloc[-12:]
    consol_range = float(consol["h"].max() - consol["l"].min())
    consol_tight = consol_range < 2 * atr
    flag = pole_strong and consol_tight
    flag_dir = "up" if pole_move > 0 else "down"
    # Pennant: consolidating tighter (slope of high < 0 AND slope of low > 0 in consol)
    h_slope = np.polyfit(range(len(consol)), consol["h"].values, 1)[0]
    l_slope = np.polyfit(range(len(consol)), consol["l"].values, 1)[0]
    pennant = pole_strong and h_slope < 0 and l_slope > 0
    # Cup & handle: 30-bar rounded bottom (low at middle of window)
    win = df.iloc[-50:] if len(df) >= 50 else df
    lo_idx = int(win["l"].argmin())
    cup = (lo_idx > len(win) * 0.3 and lo_idx < len(win) * 0.7)
    handle_lo = float(df["l"].iloc[-5:].min())
    cup_n_handle = cup and handle_lo > float(win["l"].iloc[lo_idx]) and handle_lo < float(win["c"].iloc[-1])
    payload = {"flag": flag, "flag_dir": flag_dir if flag else None,
               "pennant": pennant, "cup_and_handle": cup_n_handle,
               "pole_move_atr": round(pole_move / atr, 2)}
    if flag and flag_dir == "up":
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if flag and flag_dir == "down":
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if pennant and pole_move > 0:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if pennant and pole_move < 0:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if cup_n_handle:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class ClassicalPatternsAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
