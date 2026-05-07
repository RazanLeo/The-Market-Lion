"""Rolling Standard Deviation (period 20) of close."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "standard_deviation"; WEIGHT_DEFAULT = 0.5
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sd = float(df["c"].rolling(20).std().iloc[-1])
    avg_sd = float(df["c"].rolling(20).std().iloc[-100:].mean()) if len(df) >= 120 else sd
    ratio = sd / max(avg_sd, 1e-9)
    payload = {"std_dev": round(sd, 5), "ratio_x_avg": round(ratio, 2)}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class StandardDeviationIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
