"""Volume Charts School — bars based on volume thresholds.

A "volume bar" closes after V volume traded. Builds synthetic volume bars; color = direction.
3+ same-color volume bars = decisive directional flow.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "volume_charts"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    avg_v = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    if avg_v <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    V_threshold = avg_v * 5
    # Build synthetic volume bars
    bars = []
    open_p = float(df["c"].iloc[0])
    accumulated_v = 0
    for i in range(1, len(df)):
        p = float(df["c"].iloc[i])
        accumulated_v += float(df["v"].iloc[i])
        if accumulated_v >= V_threshold:
            bars.append((open_p, p))
            open_p = p; accumulated_v = 0
    if len(bars) < 3:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"n_vol_bars": len(bars)})
    last3 = bars[-3:]
    greens = sum(1 for o, c in last3 if c > o)
    reds = 3 - greens
    payload = {"V_threshold": round(V_threshold, 0), "n_vol_bars": len(bars),
               "last3_green": greens, "last3_red": reds}
    if greens == 3:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if reds == 3:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VolumeChartsAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
