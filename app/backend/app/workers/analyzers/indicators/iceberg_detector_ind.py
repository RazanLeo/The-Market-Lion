"""Iceberg Detector — sustained volume bursts with minimal price movement.

An iceberg = large hidden order absorbing one side. Symptom: many bars in tight range
(< 0.4×ATR) with above-average volume (> 1.5× rolling avg). 3+ consecutive such bars
signal an iceberg. Direction inferred from breakout side after the cluster.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "iceberg_detector_ind"
WEIGHT_DEFAULT = 1.05


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    vol_ma = df["v"].rolling(20).mean()
    body = (df["c"] - df["o"]).abs()
    rng = df["h"] - df["l"]
    tight = rng < (atr * 0.4)
    high_vol = df["v"] > (vol_ma * 1.5)
    iceberg_bar = (tight & high_vol).astype(int)
    streak = int(iceberg_bar.iloc[-7:].sum())
    last3 = iceberg_bar.iloc[-3:].sum()
    last_c = float(df["c"].iloc[-1])
    cluster_high = float(df["h"].iloc[-7:].max())
    cluster_low = float(df["l"].iloc[-7:].min())
    payload = {"iceberg_bars_7w": int(streak), "iceberg_bars_3w": int(last3),
               "cluster_high": round(cluster_high, 5), "cluster_low": round(cluster_low, 5)}
    if streak >= 3:
        if last_c > cluster_high * 0.999:
            return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
        if last_c < cluster_low * 1.001:
            return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
        return AnalyzerResult(CODE, "neutral", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class IcebergDetectorIndAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
