"""Lion Inertial Stochastic — modified stochastic with inertia carry.

Standard %K = (close - low_n) / (high_n - low_n). Inertial variant adds momentum
carry: K_inertial = α × K_now + (1 − α) × K_prev (α = 0.6). Smoother than raw stoch.
%D = 3-bar SMA of K_inertial. Trend filter: only signal in line with EMA50 slope.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_inertial_stoch_ind"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    n = 14
    low_n = df["l"].rolling(n).min()
    high_n = df["h"].rolling(n).max()
    k_raw = (df["c"] - low_n) / (high_n - low_n + 1e-9) * 100
    alpha = 0.6
    k_inertial = k_raw.copy()
    for i in range(1, len(k_inertial)):
        if pd.notna(k_inertial.iloc[i - 1]) and pd.notna(k_raw.iloc[i]):
            k_inertial.iloc[i] = alpha * k_raw.iloc[i] + (1 - alpha) * k_inertial.iloc[i - 1]
    d = k_inertial.rolling(3).mean()
    ema50 = df["c"].ewm(span=50, adjust=False).mean()
    trend_up = float(ema50.iloc[-1]) > float(ema50.iloc[-5])
    k_now = float(k_inertial.iloc[-1]); k_prev = float(k_inertial.iloc[-2])
    d_now = float(d.iloc[-1]); d_prev = float(d.iloc[-2])
    cross_up = k_prev < d_prev and k_now > d_now
    cross_dn = k_prev > d_prev and k_now < d_now
    payload = {"K_inertial": round(k_now, 1), "D": round(d_now, 1),
               "cross": "up" if cross_up else "down" if cross_dn else "none",
               "trend_filter": "up" if trend_up else "down"}
    if cross_up and trend_up and k_now < 30:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if cross_dn and not trend_up and k_now > 70:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionInertialStochIndAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
