"""Stan Weinstein Stage Analysis — 4 stages around the 30-period SMA (proxy for 30-week).

Stage 1: Basing — price flat, near or at 30-MA, slope ~0, low volatility.
Stage 2: Advancing — price > 30-MA AND 30-MA slope rising; the trade-able stage.
Stage 3: Topping — price flat at peak after Stage 2; 30-MA slope flattening.
Stage 4: Declining — price < 30-MA AND 30-MA slope falling.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "weinstein_stage_analysis"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    sma30 = c.rolling(30).mean()
    last = float(c.iloc[-1])
    sma_now = float(sma30.iloc[-1])
    sma_prev = float(sma30.iloc[-10]) if not pd.isna(sma30.iloc[-10]) else sma_now
    slope_pct = (sma_now - sma_prev) / sma_prev * 100 if sma_prev else 0
    above = last > sma_now
    # Volatility / range proxy
    rng_recent = float((df["h"].iloc[-30:] - df["l"].iloc[-30:]).mean())
    rng_prior = float((df["h"].iloc[-60:-30] - df["l"].iloc[-60:-30]).mean()) or rng_recent
    vol_ratio = rng_recent / rng_prior if rng_prior else 1.0
    transition = False
    if above and slope_pct > 0.4: stage = 2
    elif above and -0.2 <= slope_pct <= 0.4: stage = 3
    elif (not above) and slope_pct < -0.4: stage = 4
    else: stage = 1
    # Stage transition detection: was below + slope flipping up = 1→2
    if not above and slope_pct > 0.5 and (
        len(c) > 50 and c.iloc[-30] < sma30.iloc[-30]):
        transition = True; stage = 2
    payload = {"stage": stage, "above_sma30": above, "sma30_slope_pct": round(slope_pct, 3),
               "volatility_ratio": round(vol_ratio, 2), "transition_to_stage2": transition}
    if stage == 2: return AnalyzerResult(CODE, "buy", 75 if transition else 60, WEIGHT_DEFAULT, payload)
    if stage == 4: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if stage == 3: return AnalyzerResult(CODE, "sell", 35, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class WeinsteinStageAnalysisAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
