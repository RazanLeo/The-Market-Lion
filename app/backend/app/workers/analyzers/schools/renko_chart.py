"""Renko Chart School — synthetic Renko bricks, trend by streak.

Brick size = ATR(14). Counts streak of last same-color bricks. 5+ same = strong trend.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "renko_chart"
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
    bricks = []
    last_close = float(closes.iloc[0])
    for p in closes.iloc[1:]:
        p = float(p); diff = p - last_close
        n = int(abs(diff) / brick)
        if n >= 1:
            for _ in range(n):
                if diff > 0: bricks.append(+1); last_close += brick
                else: bricks.append(-1); last_close -= brick
    if len(bricks) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"n_bricks": len(bricks)})
    streak = 1
    for i in range(len(bricks) - 2, -1, -1):
        if bricks[i] == bricks[-1]: streak += 1
        else: break
    last_color = "green" if bricks[-1] == +1 else "red"
    payload = {"brick_size": round(brick, 5), "n_bricks": len(bricks),
               "last_color": last_color, "streak": streak}
    if last_color == "green" and streak >= 5:
        return AnalyzerResult(CODE, "buy", min(85, 50 + streak * 5), WEIGHT_DEFAULT, payload)
    if last_color == "red" and streak >= 5:
        return AnalyzerResult(CODE, "sell", min(85, 50 + streak * 5), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class RenkoChartAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
