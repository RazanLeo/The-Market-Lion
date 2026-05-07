"""Lion ARC Indicator — bar closes beyond 20-bar extreme + volume + range expansion.

Trigger:
  close > 20-bar high (ARC up) OR close < 20-bar low (ARC down)
  AND volume > 1.5× rolling 20-bar avg
  AND bar range >= 1.5×ATR(14)
Strength = sum of standardized excesses.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_arc_indicator"
WEIGHT_DEFAULT = 1.15


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_c = float(df["c"].iloc[-1])
    prev_high = float(df["h"].iloc[-21:-1].max())
    prev_low = float(df["l"].iloc[-21:-1].min())
    atr = float(_atr(df).iloc[-1] or 0)
    bar_range = float(df["h"].iloc[-1] - df["l"].iloc[-1])
    vol_avg = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    vol_now = float(df["v"].iloc[-1])
    vol_factor = vol_now / vol_avg if vol_avg > 0 else 0
    range_factor = bar_range / atr if atr > 0 else 0
    arc_up = last_c > prev_high and vol_factor > 1.5 and range_factor >= 1.5
    arc_dn = last_c < prev_low and vol_factor > 1.5 and range_factor >= 1.5
    strength = (vol_factor - 1.5 + range_factor - 1.5) * 30 if (arc_up or arc_dn) else 0
    payload = {"arc_up": arc_up, "arc_dn": arc_dn,
               "vol_factor": round(vol_factor, 2), "range_factor": round(range_factor, 2),
               "strength": round(strength, 1)}
    if arc_up:
        return AnalyzerResult(CODE, "buy", min(90, 55 + strength), WEIGHT_DEFAULT, payload)
    if arc_dn:
        return AnalyzerResult(CODE, "sell", min(90, 55 + strength), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionArcIndicatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
