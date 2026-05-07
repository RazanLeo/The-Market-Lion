"""Momentum School — composite of ROC(10) + ROC(20) + Stochastic Momentum Index + RSI slope.

Stochastic Momentum Index (SMI) uses double-smoothed EMA of (close - midpoint of N-bar range).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "momentum_school"
WEIGHT_DEFAULT = 1.0


def _smi(c: pd.Series, h: pd.Series, l: pd.Series, n: int = 14, m: int = 3) -> pd.Series:
    hh = h.rolling(n).max(); ll = l.rolling(n).min()
    mid = (hh + ll) / 2
    diff = c - mid
    rng = (hh - ll)
    ema_diff = diff.ewm(span=m, adjust=False).mean().ewm(span=m, adjust=False).mean()
    ema_rng = rng.ewm(span=m, adjust=False).mean().ewm(span=m, adjust=False).mean()
    return 100 * ema_diff / (ema_rng / 2).replace(0, 1e-9)


def _rsi(c: pd.Series, p: int = 14) -> pd.Series:
    delta = c.diff()
    up = delta.where(delta > 0, 0).ewm(alpha=1 / p, adjust=False).mean()
    dn = -delta.where(delta < 0, 0).ewm(alpha=1 / p, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    roc10 = float((c.iloc[-1] - c.iloc[-11]) / c.iloc[-11] * 100)
    roc20 = float((c.iloc[-1] - c.iloc[-21]) / c.iloc[-21] * 100)
    smi_val = float(_smi(c, df["h"], df["l"]).iloc[-1])
    rsi_v = _rsi(c)
    rsi_slope = float(rsi_v.iloc[-1] - rsi_v.iloc[-5])
    score = (1 if roc10 > 0 else -1) + (1 if roc20 > 0 else -1) \
        + (1 if smi_val > 0 else -1) + (1 if rsi_slope > 0 else -1)
    payload = {"roc10": round(roc10, 2), "roc20": round(roc20, 2),
               "smi": round(smi_val, 2), "rsi_slope_5bars": round(rsi_slope, 2),
               "score_neg4_to_pos4": score}
    if score >= 3: return AnalyzerResult(CODE, "buy", min(85.0, 50 + score * 8), WEIGHT_DEFAULT, payload)
    if score <= -3: return AnalyzerResult(CODE, "sell", min(85.0, 50 + abs(score) * 8), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MomentumSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
