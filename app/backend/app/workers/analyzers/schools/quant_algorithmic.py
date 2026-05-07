"""Quant Algorithmic — composite of mean-reversion + 12-1 momentum + volatility regime.

  • Mean reversion: Z-score of close vs SMA50.
  • Momentum: 12-period ROC minus 1-period ROC (avoids short-term noise).
  • Volatility regime: ATR(14) percentile vs last 100 bars.
Bullish if Z<-1 AND momentum>0 AND vol regime is normal/low (no extreme).
Bearish mirror.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "quant_algorithmic"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 100:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    sma50 = c.rolling(50).mean()
    sd50 = c.rolling(50).std().replace(0, 1e-9)
    z = float((c.iloc[-1] - sma50.iloc[-1]) / sd50.iloc[-1])
    roc12 = float((c.iloc[-1] - c.iloc[-13]) / c.iloc[-13] * 100)
    roc1 = float((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2] * 100)
    momentum = roc12 - roc1
    h, l = df["h"], df["l"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    last100 = atr.iloc[-100:].dropna()
    vol_pct = float((last100 <= atr.iloc[-1]).sum() / len(last100)) if len(last100) else 0.5
    extreme_vol = vol_pct > 0.85 or vol_pct < 0.15
    payload = {"z_score": round(z, 2), "momentum_12_1": round(momentum, 2),
               "vol_percentile": round(vol_pct, 2), "extreme_vol": extreme_vol}
    if extreme_vol:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {**payload, "reason": "skip_extreme_vol"})
    score = 0
    if z < -1: score += 25
    if z > 1: score -= 25
    if momentum > 1: score += 25
    if momentum < -1: score -= 25
    if score >= 30: return AnalyzerResult(CODE, "buy", min(85.0, 45 + score), WEIGHT_DEFAULT, payload)
    if score <= -30: return AnalyzerResult(CODE, "sell", min(85.0, 45 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class QuantAlgorithmicAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
