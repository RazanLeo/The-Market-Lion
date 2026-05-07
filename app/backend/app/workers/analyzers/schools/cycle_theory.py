"""Cycle Theory — dominant cycle period via autocorrelation peak detection on detrended closes.

Steps:
  1. Detrend price using linear regression residuals over last 200 bars.
  2. Compute autocorrelation up to lag 100.
  3. Locate the first prominent positive peak after lag 5 → dominant period T.
  4. Phase = (bars_since_last_low % T) / T.
  5. Project next high/low.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "cycle_theory"
WEIGHT_DEFAULT = 0.9


def _detrend(arr: np.ndarray) -> np.ndarray:
    x = np.arange(len(arr))
    slope, intercept = np.polyfit(x, arr, 1)
    return arr - (slope * x + intercept)


def _autocorr_peak(detrended: np.ndarray, max_lag: int = 100) -> tuple[int, float]:
    n = len(detrended)
    if n < max_lag * 2:
        return 0, 0.0
    mean = detrended.mean()
    var = detrended.var() or 1e-9
    acs: list[float] = []
    for k in range(1, max_lag + 1):
        a = detrended[:-k] - mean
        b = detrended[k:] - mean
        acs.append(float(np.dot(a, b) / (n - k) / var))
    # Find the first peak after lag=5 that is local max and value > 0.15
    best_lag, best_val = 0, 0.0
    for lag in range(5, max_lag - 1):
        if acs[lag] > acs[lag - 1] and acs[lag] > acs[lag + 1] and acs[lag] > 0.15:
            if acs[lag] > best_val:
                best_lag = lag + 1; best_val = acs[lag]
            break
    return best_lag, best_val


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    arr = df["c"].iloc[-200:].to_numpy()
    detrended = _detrend(arr)
    period, strength = _autocorr_peak(detrended, max_lag=80)
    if period == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"reason": "no_clear_cycle"})

    # Phase: locate last cycle low
    last_low_in_window = int(np.argmin(detrended[-period:]))
    bars_since_low = len(detrended) - 1 - (len(detrended) - period + last_low_in_window)
    phase = bars_since_low / period
    payload = {
        "period_bars": period, "strength": round(strength, 3),
        "phase": round(phase, 3),
        "bars_since_cycle_low": bars_since_low,
    }
    # Bias: 0-0.4 of cycle = mark-up phase → buy; 0.5-0.9 = distribution/decline → sell.
    if phase < 0.4:
        return AnalyzerResult(CODE, "buy", min(70.0, 40 + strength * 100), WEIGHT_DEFAULT, payload)
    if 0.5 < phase < 0.9:
        return AnalyzerResult(CODE, "sell", min(70.0, 40 + strength * 100), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)


class CycleTheoryAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
