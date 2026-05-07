"""Bill Williams Chaos — Alligator + Awesome Oscillator + 5-bar Fractals.

Alligator (median = (H+L)/2):
  Jaw  = SMA(13) shifted forward by 8
  Teeth = SMA(8)  shifted by 5
  Lips  = SMA(5)  shifted by 3
Awesome Oscillator: SMA(median, 5) - SMA(median, 34).
Bullish: Lips > Teeth > Jaw (alligator open up) + AO > 0 + last 5-bar fractal up confirmed.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fractal_chaos"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    median = (df["h"] + df["l"]) / 2
    jaw = median.rolling(13).mean().shift(8)
    teeth = median.rolling(8).mean().shift(5)
    lips = median.rolling(5).mean().shift(3)
    j, t, lp = float(jaw.iloc[-1]), float(teeth.iloc[-1]), float(lips.iloc[-1])
    open_up = lp > t > j
    open_down = lp < t < j
    sleeping = abs(lp - t) < median.iloc[-1] * 0.001
    ao = (median.rolling(5).mean() - median.rolling(34).mean())
    last_ao = float(ao.iloc[-1]); prev_ao = float(ao.iloc[-2])
    ao_cross_up = prev_ao <= 0 and last_ao > 0
    ao_cross_dn = prev_ao >= 0 and last_ao < 0
    # Fractals: 5-bar
    n = 2
    last_up_frac = None; last_dn_frac = None
    for i in range(len(df) - 3, max(len(df) - 30, 2), -1):
        if (df["h"].iloc[i] > df["h"].iloc[i - 1] and df["h"].iloc[i] > df["h"].iloc[i - 2]
                and df["h"].iloc[i] > df["h"].iloc[i + 1] and df["h"].iloc[i] > df["h"].iloc[i + 2]):
            last_up_frac = float(df["h"].iloc[i]); break
    for i in range(len(df) - 3, max(len(df) - 30, 2), -1):
        if (df["l"].iloc[i] < df["l"].iloc[i - 1] and df["l"].iloc[i] < df["l"].iloc[i - 2]
                and df["l"].iloc[i] < df["l"].iloc[i + 1] and df["l"].iloc[i] < df["l"].iloc[i + 2]):
            last_dn_frac = float(df["l"].iloc[i]); break
    last_close = float(df["c"].iloc[-1])
    broke_up = last_up_frac and last_close > last_up_frac
    broke_dn = last_dn_frac and last_close < last_dn_frac
    payload = {"jaw": round(j, 5), "teeth": round(t, 5), "lips": round(lp, 5),
               "alligator_open_up": open_up, "alligator_open_down": open_down,
               "alligator_sleeping": sleeping,
               "ao": round(last_ao, 5), "ao_cross_up": ao_cross_up, "ao_cross_down": ao_cross_dn,
               "broke_up_fractal": broke_up, "broke_dn_fractal": broke_dn}
    if open_up and ao_cross_up and broke_up:
        return AnalyzerResult(CODE, "buy", 85, WEIGHT_DEFAULT, payload)
    if open_down and ao_cross_dn and broke_dn:
        return AnalyzerResult(CODE, "sell", 85, WEIGHT_DEFAULT, payload)
    if open_up and last_ao > 0:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if open_down and last_ao < 0:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FractalChaosAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
