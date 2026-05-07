"""Lion Liquidity Sweep Detector.

A "sweep" = wick that pierces a recent major swing high/low THEN closes back inside the
prior range within 1-3 bars. Indicates stop-hunt followed by reversal.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_liquidity_sweeps_detector"
WEIGHT_DEFAULT = 1.1


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-30:]
    swing_high = float(win["h"].iloc[:-3].max())
    swing_low = float(win["l"].iloc[:-3].min())
    last3 = win.iloc[-3:]
    bull_sweep = bool(last3["l"].min() < swing_low and float(last3["c"].iloc[-1]) > swing_low)
    bear_sweep = bool(last3["h"].max() > swing_high and float(last3["c"].iloc[-1]) < swing_high)
    sweep_strength = 0
    if bull_sweep:
        wick_depth = (swing_low - float(last3["l"].min())) / (float(last3["h"].max()) - float(last3["l"].min()) + 1e-9)
        sweep_strength = wick_depth * 100
    if bear_sweep:
        wick_depth = (float(last3["h"].max()) - swing_high) / (float(last3["h"].max()) - float(last3["l"].min()) + 1e-9)
        sweep_strength = wick_depth * 100
    payload = {"swing_high": round(swing_high, 5), "swing_low": round(swing_low, 5),
               "bull_sweep": bull_sweep, "bear_sweep": bear_sweep,
               "reversal_strength": round(sweep_strength, 1)}
    if bull_sweep:
        return AnalyzerResult(CODE, "buy", min(85, 55 + sweep_strength), WEIGHT_DEFAULT, payload)
    if bear_sweep:
        return AnalyzerResult(CODE, "sell", min(85, 55 + sweep_strength), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionLiquiditySweepsDetectorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
