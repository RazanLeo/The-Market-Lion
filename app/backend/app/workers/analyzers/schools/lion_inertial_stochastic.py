"""Lion Inertial Stochastic — Stochastic K/D with WMA(5) smoothing and trend confirmation.

%K standard 14-period, %D = WMA(5) of %K (linear weights 1..5).
Crossings have additional weight when ADX > 20 ("trending market").
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_inertial_stochastic"
WEIGHT_DEFAULT = 0.85


def _wma(s: pd.Series, n: int = 5) -> pd.Series:
    weights = np.arange(1, n + 1)
    return s.rolling(n).apply(lambda x: float(np.dot(x, weights) / weights.sum()), raw=False)


def _adx(df: pd.DataFrame) -> float:
    h, l, c = df["h"], df["l"], df["c"]
    up = h.diff(); dn = -l.diff()
    pdm = up.where((up > dn) & (up > 0), 0); ndm = dn.where((dn > up) & (dn > 0), 0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1/14, adjust=False).mean() / atr.replace(0, 1e-9)
    ndi = 100 * ndm.ewm(alpha=1/14, adjust=False).mean() / atr.replace(0, 1e-9)
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, 1e-9)
    return float(dx.ewm(alpha=1/14, adjust=False).mean().iloc[-1])


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    ll = l.rolling(14).min(); hh = h.rolling(14).max()
    k = 100 * (c - ll) / (hh - ll + 1e-9)
    d = _wma(k, 5)
    K, D = float(k.iloc[-1]), float(d.iloc[-1])
    Kp, Dp = float(k.iloc[-2]), float(d.iloc[-2])
    cross_up = Kp <= Dp and K > D
    cross_dn = Kp >= Dp and K < D
    adx = _adx(df)
    confirmed = adx > 20
    payload = {"K": round(K, 1), "D": round(D, 1),
               "cross_up": cross_up, "cross_down": cross_dn,
               "adx": round(adx, 1), "trend_confirmed": confirmed}
    if cross_up:
        return AnalyzerResult(CODE, "buy", 80 if confirmed else 55, WEIGHT_DEFAULT, payload)
    if cross_dn:
        return AnalyzerResult(CODE, "sell", 80 if confirmed else 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionInertialStochasticAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
