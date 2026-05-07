"""Cumulative Volume Delta (CVD) — Σ sign(close-open) × volume.

CVD is the running total of signed volume (volume on up-bars minus volume on down-bars).
Divergences between price and CVD are key reversal signals: price makes new high but
CVD does not = bearish divergence.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "cumulative_volume_delta"
WEIGHT_DEFAULT = 1.05


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sign = np.sign(df["c"] - df["o"]).fillna(0)
    delta = sign * df["v"]
    cvd = delta.cumsum()
    last_cvd = float(cvd.iloc[-1])
    cvd_20 = cvd.iloc[-20:]
    p_20 = df["c"].iloc[-20:]
    p_high_idx = int(p_20.argmax()); p_low_idx = int(p_20.argmin())
    cvd_high_idx = int(cvd_20.argmax()); cvd_low_idx = int(cvd_20.argmin())
    bear_div = (p_high_idx >= 15 and cvd_high_idx < p_high_idx - 3 and
                float(p_20.iloc[-1]) >= float(p_20.iloc[p_high_idx]) * 0.99)
    bull_div = (p_low_idx >= 15 and cvd_low_idx < p_low_idx - 3 and
                float(p_20.iloc[-1]) <= float(p_20.iloc[p_low_idx]) * 1.01)
    cvd_slope = float(cvd.iloc[-1] - cvd.iloc[-10]) / 10
    payload = {"cvd": round(last_cvd, 2), "cvd_slope_10b": round(cvd_slope, 2),
               "bullish_divergence": bull_div, "bearish_divergence": bear_div}
    if bull_div:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if bear_div:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if cvd_slope > 0 and float(df["c"].iloc[-1]) > float(df["c"].iloc[-5]):
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if cvd_slope < 0 and float(df["c"].iloc[-1]) < float(df["c"].iloc[-5]):
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CumulativeVolumeDeltaAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
