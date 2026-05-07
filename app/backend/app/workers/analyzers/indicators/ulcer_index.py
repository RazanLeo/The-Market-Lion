"""Ulcer Index — measures downside volatility. UI = sqrt(mean(drawdown%^2)) over n bars."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "ulcer_index"; WEIGHT_DEFAULT = 0.5
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 14
    if len(df) < n + 5: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rolling_max = df["c"].rolling(n).max()
    drawdown = ((df["c"] - rolling_max) / rolling_max.replace(0, 1e-9)) * 100
    ui = ((drawdown ** 2).rolling(n).mean()) ** 0.5
    last = float(ui.iloc[-1])
    payload = {"ulcer_index": round(last, 2)}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class UlcerIndexIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
