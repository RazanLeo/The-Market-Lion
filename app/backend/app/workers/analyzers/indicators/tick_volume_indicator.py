"""Tick Volume Indicator — proxy of trade-count from volume (forex-style).

In FX/CFDs there is no real volume; "tick volume" = number of price changes per bar.
We estimate tick activity using high-low range variability:
  tick_proxy = v / atr(14)
Higher ratio = more ticks per unit price = active session. Combined with EMA(20) of
proxy to detect activity surges (signal candidates).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "tick_volume_indicator"
WEIGHT_DEFAULT = 0.65


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    proxy = df["v"] / atr.replace(0, 1e-9)
    proxy_ma = proxy.rolling(20).mean()
    last = float(proxy.iloc[-1])
    avg = float(proxy_ma.iloc[-1] or 0)
    surge = last > avg * 1.5 if avg > 0 else False
    direction = float(df["c"].iloc[-1]) - float(df["o"].iloc[-1])
    payload = {"tick_proxy": round(last, 3), "avg_20b": round(avg, 3),
               "surge": surge, "bar_direction": "up" if direction > 0 else "down"}
    if surge and direction > 0:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if surge and direction < 0:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class TickVolumeIndicatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
