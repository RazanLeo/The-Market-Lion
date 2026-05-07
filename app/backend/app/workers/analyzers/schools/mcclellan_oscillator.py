"""McClellan Oscillator — EMA(19) - EMA(39) of advance-decline net.

For a single-instrument proxy we use the per-bar net = sign(close-prev_close) × volume.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "mcclellan_oscillator"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sgn = np.sign(df["c"].diff().fillna(0))
    net = sgn * df["v"].fillna(0)
    ema19 = net.ewm(span=19, adjust=False).mean()
    ema39 = net.ewm(span=39, adjust=False).mean()
    mo = ema19 - ema39
    last = float(mo.iloc[-1]); prev = float(mo.iloc[-2])
    rolling_std = float(mo.rolling(60).std().iloc[-1] or 1)
    z = last / rolling_std
    cross_up = prev <= 0 and last > 0
    cross_dn = prev >= 0 and last < 0

    payload = {"value": round(last, 2), "z_score": round(z, 2),
               "zero_cross_up": cross_up, "zero_cross_down": cross_dn}
    if cross_up: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if cross_dn: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if z > 1.5: return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if z < -1.5: return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class McclellanOscillatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
