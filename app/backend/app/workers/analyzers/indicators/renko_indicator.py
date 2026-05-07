"""Renko Bricks — fixed-size price bricks; trend = direction of last N bricks.

Each brick has height = ATR(14)×1. New brick added when price moves brick_size in one
direction without first moving 2×brick_size against. Counts consecutive same-color
bricks. 5+ green = strong uptrend, 5+ red = strong downtrend.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "renko_indicator"
WEIGHT_DEFAULT = 0.85


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    brick = _atr(df)
    if brick <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    closes = df["c"].iloc[-200:] if len(df) > 200 else df["c"]
    bricks = []  # list of +1 / -1
    last_brick_close = float(closes.iloc[0])
    for p in closes.iloc[1:]:
        p = float(p)
        diff = p - last_brick_close
        n_bricks = int(abs(diff) / brick)
        if n_bricks >= 1:
            for _ in range(n_bricks):
                if diff > 0:
                    bricks.append(+1); last_brick_close += brick
                else:
                    bricks.append(-1); last_brick_close -= brick
    if len(bricks) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"n_bricks": len(bricks)})
    streak = 1
    for i in range(len(bricks) - 2, -1, -1):
        if bricks[i] == bricks[-1]:
            streak += 1
        else:
            break
    last_color = "green" if bricks[-1] == +1 else "red"
    payload = {"brick_size": round(brick, 5), "n_bricks": len(bricks),
               "last_color": last_color, "current_streak": streak}
    if last_color == "green" and streak >= 5:
        return AnalyzerResult(CODE, "buy", min(85, 50 + streak * 5), WEIGHT_DEFAULT, payload)
    if last_color == "red" and streak >= 5:
        return AnalyzerResult(CODE, "sell", min(85, 50 + streak * 5), WEIGHT_DEFAULT, payload)
    if last_color == "green" and streak >= 3:
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if last_color == "red" and streak >= 3:
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class RenkoIndicatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
