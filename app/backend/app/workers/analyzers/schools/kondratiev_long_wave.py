"""Kondratiev Long Wave — economic super-cycle (~50-60 years) phase estimator.

We estimate a long-wave phase from the long-period ROC and trend persistence:
  • Annualized return over last 200 bars, normalized.
  • Volatility (std of annual returns).
Spring: rising returns, low vol.  Summer: rising returns, rising vol.
Autumn: falling returns, high vol. Winter: falling returns, declining vol.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "kondratiev_long_wave"
WEIGHT_DEFAULT = 0.6


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    log_ret = np.log(c / c.shift()).dropna()
    long_roc = float((c.iloc[-1] - c.iloc[-200]) / c.iloc[-200] * 100)
    vol_recent = float(log_ret.iloc[-50:].std() * 100)
    vol_prior = float(log_ret.iloc[-150:-50].std() * 100) or vol_recent
    rising_returns = long_roc > 0
    rising_vol = vol_recent > vol_prior * 1.05
    falling_vol = vol_recent < vol_prior * 0.95
    if rising_returns and not rising_vol: phase = "Spring"
    elif rising_returns and rising_vol: phase = "Summer"
    elif (not rising_returns) and rising_vol: phase = "Autumn"
    else: phase = "Winter"
    payload = {"phase": phase, "long_roc_pct": round(long_roc, 1),
               "vol_recent_pct": round(vol_recent, 2), "vol_prior_pct": round(vol_prior, 2)}
    if phase == "Spring": return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if phase == "Summer": return AnalyzerResult(CODE, "buy", 35, WEIGHT_DEFAULT, payload)
    if phase == "Autumn": return AnalyzerResult(CODE, "sell", 35, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)


class KondratievLongWaveAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
