"""Up/Down Volume Ratio — Σ vol(up bars) / Σ vol(down bars) over rolling N.

Up bar = c > c.shift(1); down bar = c < c.shift(1). Ratio > 1.5 = strong demand,
< 0.67 = strong supply. Trend-confirmation indicator: divergence between price and
ratio (price up but ratio dropping) signals weakening trend.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "up_down_volume_ratio"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    up = (df["c"] > df["c"].shift(1)).astype(float)
    dn = (df["c"] < df["c"].shift(1)).astype(float)
    up_vol = (df["v"] * up).rolling(20).sum()
    dn_vol = (df["v"] * dn).rolling(20).sum()
    ratio = up_vol / (dn_vol + 1e-9)
    last = float(ratio.iloc[-1] or 0)
    prev_5 = float(ratio.iloc[-6] or 0)
    price_up = float(df["c"].iloc[-1]) > float(df["c"].iloc[-6])
    payload = {"ud_vol_ratio_20": round(last, 2), "ratio_5b_ago": round(prev_5, 2),
               "price_up_5b": price_up}
    if last > 1.5 and price_up:
        return AnalyzerResult(CODE, "buy", min(80, 50 + last * 10), WEIGHT_DEFAULT, payload)
    if last < 0.67 and not price_up:
        return AnalyzerResult(CODE, "sell", min(80, 50 + (1 / max(last, 0.1)) * 10), WEIGHT_DEFAULT, payload)
    if price_up and last < prev_5 * 0.7:  # bearish divergence
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if (not price_up) and last > prev_5 * 1.3:  # bullish divergence
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class UpDownVolumeRatioAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
