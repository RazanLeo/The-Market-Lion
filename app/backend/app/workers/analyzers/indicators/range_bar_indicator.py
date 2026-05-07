"""Range Bars — synthetic bars of fixed price-range (R = ATR×0.5).

Builds a stream of synthetic bars where each bar has range exactly R. Counts the last
N bars and computes net direction:
  green_count = bars closing higher than open
  red_count   = bars closing lower
Net direction signal: persistent green ≥ 6 / 10 = buy; persistent red = sell.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "range_bar_indicator"
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
    bars = []  # list of (open, close)
    open_p = float(closes.iloc[0]); high = open_p; low = open_p
    for p in closes.iloc[1:]:
        p = float(p)
        high = max(high, p); low = min(low, p)
        if (high - low) >= R:
            close_p = p
            bars.append((open_p, close_p))
            open_p = close_p; high = open_p; low = open_p
    if len(bars) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"range_R": R, "n_bars": len(bars)})
    last_n = bars[-10:]
    greens = sum(1 for o, c in last_n if c > o)
    reds = len(last_n) - greens
    payload = {"range_R": round(R, 5), "n_synth_bars": len(bars),
               "last10_green": greens, "last10_red": reds}
    if greens >= 7:
        return AnalyzerResult(CODE, "buy", min(80, 50 + greens * 4), WEIGHT_DEFAULT, payload)
    if reds >= 7:
        return AnalyzerResult(CODE, "sell", min(80, 50 + reds * 4), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class RangeBarIndicatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
