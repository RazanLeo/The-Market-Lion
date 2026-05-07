"""Absorption Zones — heavy volume bars with minimal price movement.

Absorption = aggressive market orders being absorbed by passive liquidity. Symptom:
volume > 2× average AND |c-o| < 0.3×ATR. Bullish absorption (rejection of lows) when
absorption candle has long lower wick. Bearish absorption when long upper wick.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "absorption_zones"
WEIGHT_DEFAULT = 1.0


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    atr_now = float(atr.iloc[-1] or 0)
    vol_ma = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    if atr_now <= 0 or vol_ma <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o = float(df["o"].iloc[-1]); h = float(df["h"].iloc[-1]); l = float(df["l"].iloc[-1])
    c = float(df["c"].iloc[-1]); v = float(df["v"].iloc[-1])
    body = abs(c - o); upper_wick = h - max(o, c); lower_wick = min(o, c) - l
    is_absorption = v > vol_ma * 2 and body < atr_now * 0.3
    payload = {"is_absorption_bar": is_absorption, "vol_ratio": round(v / (vol_ma + 1e-9), 2),
               "body_atr_ratio": round(body / (atr_now + 1e-9), 3),
               "upper_wick": round(upper_wick, 5), "lower_wick": round(lower_wick, 5)}
    if is_absorption and lower_wick > body * 2 and lower_wick > upper_wick * 1.5:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if is_absorption and upper_wick > body * 2 and upper_wick > lower_wick * 1.5:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AbsorptionZonesAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
