"""Mass-Volume Ratio — Σ vol on big-range bars / Σ vol on small-range bars.

A "big bar" has range ≥ 1.5×ATR; "small bar" has range ≤ 0.7×ATR. Ratio over rolling
30 bars: > 1.5 = climactic action (large bars accumulating volume — possible exhaustion
or distribution), < 0.5 = quiet absorption (potential breakout setup).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "mass_volume_ratio"
WEIGHT_DEFAULT = 0.75


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    rng = df["h"] - df["l"]
    big = rng > (atr * 1.5)
    small = rng < (atr * 0.7)
    big_vol = (df["v"] * big).rolling(30).sum()
    small_vol = (df["v"] * small).rolling(30).sum()
    ratio = big_vol / (small_vol + 1e-9)
    last = float(ratio.iloc[-1] or 0)
    last_c = float(df["c"].iloc[-1])
    bull_dir = last_c > float(df["c"].iloc[-5])
    payload = {"mass_volume_ratio_30": round(last, 2),
               "big_bars_vol": float(big_vol.iloc[-1] or 0),
               "small_bars_vol": float(small_vol.iloc[-1] or 0)}
    if last < 0.5 and bull_dir:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)  # quiet absorption -> breakout
    if last < 0.5 and not bull_dir:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if last > 1.5:
        return AnalyzerResult(CODE, "neutral", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MassVolumeRatioAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
