"""Arms Index (TRIN) — single-instrument proxy.

Standard TRIN: (advancing issues / declining issues) / (advancing volume / declining volume).
Single-instrument proxy: rolling counts and volumes of up vs down bars over 30 bars.
TRIN < 1 = bullish, > 1 = bearish. Extremes: > 1.5 oversold, < 0.5 overbought.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "arms_index_trin"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    up = (df["c"] > df["c"].shift(1)).astype(float)
    dn = (df["c"] < df["c"].shift(1)).astype(float)
    up_count = up.rolling(30).sum()
    dn_count = dn.rolling(30).sum()
    up_vol = (df["v"] * up).rolling(30).sum()
    dn_vol = (df["v"] * dn).rolling(30).sum()
    ad_ratio = up_count / (dn_count + 1e-9)
    vol_ratio = up_vol / (dn_vol + 1e-9)
    trin = ad_ratio / (vol_ratio + 1e-9)
    last = float(trin.iloc[-1]) if not pd.isna(trin.iloc[-1]) else 1.0
    payload = {"trin": round(last, 3),
               "up_bars_30": int(up_count.iloc[-1] or 0),
               "down_bars_30": int(dn_count.iloc[-1] or 0)}
    if last > 1.5:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if last < 0.5:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if last > 1.1:
        return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    if last < 0.9:
        return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class ArmsIndexTrinAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
