"""Range Bars Chart School — synthetic range bars, trend by streak.

Synthetic bars of fixed range R = ATR × 0.5. Counts last 10 synth bars: 7+ green = strong
uptrend, 7+ red = strong downtrend.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "range_bars_chart"
WEIGHT_DEFAULT = 0.7


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    R = _atr(df) * 0.5
    if R <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    closes = df["c"].iloc[-200:] if len(df) > 200 else df["c"]
    bars = []
    open_p = float(closes.iloc[0]); high = open_p; low = open_p
    for p in closes.iloc[1:]:
        p = float(p)
        high = max(high, p); low = min(low, p)
        if (high - low) >= R:
            bars.append((open_p, p))
            open_p = p; high = open_p; low = open_p
    last10 = bars[-10:] if len(bars) >= 10 else bars
    greens = sum(1 for o, c in last10 if c > o)
    reds = len(last10) - greens
    payload = {"range_R": round(R, 5), "n_bars": len(bars),
               "last10_green": greens, "last10_red": reds}
    if greens >= 7:
        return AnalyzerResult(CODE, "buy", min(80, 50 + greens * 4), WEIGHT_DEFAULT, payload)
    if reds >= 7:
        return AnalyzerResult(CODE, "sell", min(80, 50 + reds * 4), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class RangeBarsChartAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
