"""Wilder ADX + Directional Movement Index — full implementation with regime detection.

Smoothed by Wilder method (alpha = 1/14):
  TR  = max(H-L, |H-prevC|, |L-prevC|)
  +DM = (H[t] - H[t-1])  if positive and > -DM, else 0
  -DM = (L[t-1] - L[t])  if positive and > +DM, else 0
  +DI = 100 × smooth(+DM)/smooth(TR);  -DI mirror.
  DX  = 100 × |+DI - -DI| / (+DI + -DI)
  ADX = smooth(DX)
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "adx_dmi_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    up = h.diff()
    dn = -l.diff()
    plus_dm = up.where((up > dn) & (up > 0), 0)
    minus_dm = dn.where((dn > up) & (dn > 0), 0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr_w = tr.ewm(alpha=1/14, adjust=False).mean()
    pdi = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_w.replace(0, 1e-9)
    mdi = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_w.replace(0, 1e-9)
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, 1e-9)
    adx = dx.ewm(alpha=1/14, adjust=False).mean()
    last_adx = float(adx.iloc[-1])
    last_pdi = float(pdi.iloc[-1]); last_mdi = float(mdi.iloc[-1])
    prev_pdi = float(pdi.iloc[-2]); prev_mdi = float(mdi.iloc[-2])
    cross_up = prev_pdi <= prev_mdi and last_pdi > last_mdi
    cross_dn = prev_pdi >= prev_mdi and last_pdi < last_mdi
    regime = "trending" if last_adx > 25 else "ranging" if last_adx < 20 else "transitional"
    payload = {"adx": round(last_adx, 1), "+DI": round(last_pdi, 1), "-DI": round(last_mdi, 1),
               "regime": regime, "DI_cross_up": cross_up, "DI_cross_down": cross_dn}
    if cross_up and last_adx > 20:
        return AnalyzerResult(CODE, "buy", min(85.0, 50 + last_adx), WEIGHT_DEFAULT, payload)
    if cross_dn and last_adx > 20:
        return AnalyzerResult(CODE, "sell", min(85.0, 50 + last_adx), WEIGHT_DEFAULT, payload)
    if last_adx > 25 and last_pdi > last_mdi:
        return AnalyzerResult(CODE, "buy", min(70.0, 35 + last_adx * 0.5), WEIGHT_DEFAULT, payload)
    if last_adx > 25 and last_mdi > last_pdi:
        return AnalyzerResult(CODE, "sell", min(70.0, 35 + last_adx * 0.5), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AdxDmiSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
