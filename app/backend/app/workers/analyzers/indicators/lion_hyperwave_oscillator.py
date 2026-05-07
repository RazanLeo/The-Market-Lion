"""Lion Hyperwave Oscillator — derivative of price slope.

Hyperwave detects unsustainable parabolic moves. Computes:
  slope_5  = avg(c.diff(5))
  slope_10 = avg(c.diff(10))
  acceleration = slope_5 - slope_10
Phase: 1 (low) → 5 (parabolic). Phase 5 = warning of imminent reversal.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_hyperwave_oscillator"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    slope_5 = float((c.iloc[-1] - c.iloc[-6]) / 5)
    slope_10 = float((c.iloc[-1] - c.iloc[-11]) / 10)
    accel = slope_5 - slope_10
    atr = pd.concat([df["h"] - df["l"],
                     (df["h"] - df["c"].shift()).abs(),
                     (df["l"] - df["c"].shift()).abs()], axis=1).max(axis=1).rolling(14).mean()
    atr_now = float(atr.iloc[-1] or 1e-9)
    accel_norm = accel / atr_now
    phase = 1
    if abs(accel_norm) > 0.05: phase = 2
    if abs(accel_norm) > 0.15: phase = 3
    if abs(accel_norm) > 0.30: phase = 4
    if abs(accel_norm) > 0.50: phase = 5
    payload = {"slope_5": round(slope_5, 6), "slope_10": round(slope_10, 6),
               "acceleration_norm": round(accel_norm, 4), "phase": phase,
               "warning": phase >= 4}
    # Phase 5 = exhaustion: fade the move
    if phase >= 5 and accel_norm > 0:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if phase >= 5 and accel_norm < 0:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if phase == 4 and accel_norm > 0:
        return AnalyzerResult(CODE, "neutral", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionHyperwaveOscillatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
