"""Mean Reversion (Quant) — Z-score + Ornstein-Uhlenbeck half-life.

Z = (price - SMA50) / std50.
Half-life from lag-1 autocorrelation: HL = -ln(2)/ln(rho1) bars.
A market with HL < 30 bars is mean-reverting; trade pullbacks at |Z| > 2.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "mean_reversion_quant"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 100:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    sma50 = c.rolling(50).mean()
    std50 = c.rolling(50).std().replace(0, 1e-9)
    z = (c - sma50) / std50
    z_last = float(z.iloc[-1])
    # Lag-1 autocorrelation of detrended series
    detrended = (c - sma50).dropna().to_numpy()
    if len(detrended) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rho1 = float(np.corrcoef(detrended[:-1], detrended[1:])[0, 1])
    if rho1 <= 0 or rho1 >= 1:
        half_life = float("inf")
    else:
        half_life = -math.log(2) / math.log(rho1)
    is_mean_reverting = half_life < 30
    payload = {"z_score": round(z_last, 3), "rho1": round(rho1, 3),
               "half_life_bars": round(half_life, 1) if half_life != float("inf") else None,
               "is_mean_reverting": is_mean_reverting}
    if not is_mean_reverting:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    if z_last < -2:
        return AnalyzerResult(CODE, "buy", min(85.0, 50 + abs(z_last) * 12), WEIGHT_DEFAULT, payload)
    if z_last > 2:
        return AnalyzerResult(CODE, "sell", min(85.0, 50 + abs(z_last) * 12), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MeanReversionQuantAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
