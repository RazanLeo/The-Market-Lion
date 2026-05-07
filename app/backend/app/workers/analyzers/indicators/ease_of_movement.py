"""Ease of Movement: ((H+L)/2 - (H[-1]+L[-1])/2) / (V/(H-L)). SMA(14) smoothing."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "ease_of_movement"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    mid = (df["h"] + df["l"]) / 2
    dm = mid - mid.shift()
    box = df["v"].fillna(1) / (df["h"] - df["l"] + 1e-9)
    eom = (dm / box).rolling(14).mean()
    last = float(eom.iloc[-1])
    payload = {"eom": round(last, 5)}
    if last > 0: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if last < 0: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class EaseOfMovementIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
