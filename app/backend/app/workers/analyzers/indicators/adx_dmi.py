"""Wilder ADX + Directional Movement (period 14)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "adx_dmi"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    up = h.diff(); dn = -l.diff()
    pdm = up.where((up > dn) & (up > 0), 0); ndm = dn.where((dn > up) & (dn > 0), 0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1/14, adjust=False).mean() / atr.replace(0, 1e-9)
    ndi = 100 * ndm.ewm(alpha=1/14, adjust=False).mean() / atr.replace(0, 1e-9)
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, 1e-9)
    adx = dx.ewm(alpha=1/14, adjust=False).mean()
    A, P, N = float(adx.iloc[-1]), float(pdi.iloc[-1]), float(ndi.iloc[-1])
    payload = {"adx": round(A, 1), "+DI": round(P, 1), "-DI": round(N, 1)}
    if A > 25 and P > N: return AnalyzerResult(CODE, "buy", min(80.0, 45 + A), WEIGHT_DEFAULT, payload)
    if A > 25 and N > P: return AnalyzerResult(CODE, "sell", min(80.0, 45 + A), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class AdxDmiIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
