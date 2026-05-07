"""Commodity Selection Index (CSI) — Wilder's CSI = ADX × ATR × scaling.

Wilder's CSI ranks commodities by directional movement strength. Formula:
  CSI = ADX(14) × ATR(14) × (V × M) / sqrt(margin)
where V = volatility-adjustment, M = margin requirement. We simplify to
CSI_proxy = ADX × ATR × (close / 100). Higher CSI = stronger trend, more selectable.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "commodity_selection_index"
WEIGHT_DEFAULT = 0.7


def _adx_atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    up_move = h - h.shift()
    dn_move = l.shift() - l
    plus_dm = ((up_move > dn_move) & (up_move > 0)) * up_move.clip(lower=0)
    minus_dm = ((dn_move > up_move) & (dn_move > 0)) * dn_move.clip(lower=0)
    plus_di = 100 * plus_dm.ewm(alpha=1 / n, adjust=False).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1 / n, adjust=False).mean() / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    adx = dx.ewm(alpha=1 / n, adjust=False).mean()
    return adx, atr


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    adx, atr = _adx_atr(df)
    last_c = float(df["c"].iloc[-1])
    csi = float(adx.iloc[-1] or 0) * float(atr.iloc[-1] or 0) * (last_c / 100)
    csi_ma = (adx * atr * (df["c"] / 100)).rolling(20).mean()
    csi_avg = float(csi_ma.iloc[-1] or 0)
    payload = {"csi": round(csi, 4), "csi_avg_20": round(csi_avg, 4),
               "adx": round(float(adx.iloc[-1] or 0), 2),
               "atr": round(float(atr.iloc[-1] or 0), 5)}
    if csi > csi_avg * 1.3 and float(adx.iloc[-1]) > 25:
        direction_up = float(df["c"].iloc[-1]) > float(df["c"].iloc[-10])
        return AnalyzerResult(CODE, "buy" if direction_up else "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CommoditySelectionIndexAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
