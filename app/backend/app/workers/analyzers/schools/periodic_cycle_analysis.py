"""Periodic Cycle Analysis — dominant period via simplified DFT over detrended price.

We compute the discrete Fourier transform of (close - SMA50) and pick the period
with highest power in the 4-128 bar range. Project the next peak/trough.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "periodic_cycle_analysis"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    arr = df["c"].iloc[-256:].to_numpy()
    detr = arr - pd.Series(arr).rolling(50).mean().fillna(arr.mean()).to_numpy()
    fft = np.fft.fft(detr)
    freqs = np.fft.fftfreq(len(detr))
    power = np.abs(fft) ** 2
    # restrict period 4-128 bars
    valid = []
    for i in range(1, len(freqs) // 2):
        period = 1 / freqs[i]
        if 4 <= period <= 128:
            valid.append((i, period, power[i]))
    if not valid:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    best_i, best_period, best_power = max(valid, key=lambda x: x[2])
    # Estimate phase
    phase_rad = float(np.angle(fft[best_i]))
    bars_to_next_peak = ((np.pi - phase_rad) / (2 * np.pi)) * best_period
    if bars_to_next_peak < 0: bars_to_next_peak += best_period
    bars_to_next_trough = (bars_to_next_peak + best_period / 2) % best_period
    payload = {"dominant_period_bars": round(float(best_period), 1),
               "phase_rad": round(phase_rad, 3),
               "bars_to_next_peak": round(bars_to_next_peak, 1),
               "bars_to_next_trough": round(bars_to_next_trough, 1)}
    if bars_to_next_trough < 3:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if bars_to_next_peak < 3:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class PeriodicCycleAnalysisAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
