"""Anchored VWAP — VWAP from a chosen anchor (most recent swing low).

VWAP = Σ(typical × volume) / Σ(volume) starting at anchor bar.
±1σ and ±2σ bands derived from variance of typical price weighted by volume.
Bullish bias when close is above anchored VWAP and rising; rejection from VWAP top
(close below) signals weakening trend.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "anchored_vwap"
WEIGHT_DEFAULT = 1.05


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-150:] if len(df) > 150 else df
    anchor = int(win["l"].argmin())
    seg = win.iloc[anchor:]
    if len(seg) < 10:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    typical = (seg["h"] + seg["l"] + seg["c"]) / 3
    vol = seg["v"].clip(lower=0)
    cum_v = vol.cumsum()
    cum_pv = (typical * vol).cumsum()
    vwap = cum_pv / cum_v.replace(0, np.nan)
    var = ((typical - vwap) ** 2 * vol).cumsum() / cum_v.replace(0, np.nan)
    sigma = np.sqrt(var)
    last_c = float(df["c"].iloc[-1])
    last_vwap = float(vwap.iloc[-1]); last_sig = float(sigma.iloc[-1] or 0)
    band_u1 = last_vwap + last_sig; band_l1 = last_vwap - last_sig
    band_u2 = last_vwap + 2 * last_sig; band_l2 = last_vwap - 2 * last_sig
    payload = {"anchor_bar": int(anchor), "anchored_vwap": round(last_vwap, 5),
               "sigma": round(last_sig, 5), "upper_1": round(band_u1, 5),
               "lower_1": round(band_l1, 5), "upper_2": round(band_u2, 5),
               "lower_2": round(band_l2, 5)}
    if last_c < band_l2:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last_c > band_u2:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if last_c > last_vwap and float(df["c"].iloc[-1]) > float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if last_c < last_vwap and float(df["c"].iloc[-1]) < float(df["c"].iloc[-3]):
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AnchoredVwapAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
