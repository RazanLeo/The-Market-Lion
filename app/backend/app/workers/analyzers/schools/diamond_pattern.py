"""Diamond Pattern — broadening (5 expanding swings) followed by narrowing (5 contracting swings).

We measure swing-to-swing range over the last ~10-12 alternating swings.
First half: ranges should expand (each new high higher than prior, each new low lower).
Second half: ranges should contract (each new high lower, each new low higher).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "diamond_pattern"
WEIGHT_DEFAULT = 0.85


def _swings(df: pd.DataFrame, n: int = 3):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 3)
    if len(pivs) < 9:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    last9 = pivs[-9:]
    highs = [p[2] for p in last9 if p[1] == "H"]
    lows = [p[2] for p in last9 if p[1] == "L"]
    if len(highs) < 4 or len(lows) < 4:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    half = len(highs) // 2
    expanding_h = all(highs[i + 1] > highs[i] for i in range(half - 1))
    contracting_h = all(highs[i + 1] < highs[i] for i in range(half, len(highs) - 1))
    expanding_l = all(lows[i + 1] < lows[i] for i in range(half - 1))
    contracting_l = all(lows[i + 1] > lows[i] for i in range(half, len(lows) - 1))

    is_diamond = expanding_h and expanding_l and contracting_h and contracting_l
    if not is_diamond:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {
            "expanding_h": expanding_h, "expanding_l": expanding_l,
            "contracting_h": contracting_h, "contracting_l": contracting_l,
        })

    # Determine top/bottom: if the diamond formed at relative high vs. price 80 bars ago, it's a top.
    is_top = float(df["c"].iloc[-1]) > float(df["c"].iloc[-80]) * 1.02
    last_close = float(df["c"].iloc[-1])
    payload = {
        "diamond": "top" if is_top else "bottom",
        "highs_seq": [round(h, 5) for h in highs],
        "lows_seq": [round(l, 5) for l in lows],
    }
    # Side: top → bearish breakout below most recent low; bottom → bullish breakout above last high
    if is_top and last_close < min(lows[-3:]):
        return AnalyzerResult(CODE, "sell", 75.0, WEIGHT_DEFAULT, {**payload, "breakout": "downside"})
    if (not is_top) and last_close > max(highs[-3:]):
        return AnalyzerResult(CODE, "buy", 75.0, WEIGHT_DEFAULT, {**payload, "breakout": "upside"})
    return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)


class DiamondPatternAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
