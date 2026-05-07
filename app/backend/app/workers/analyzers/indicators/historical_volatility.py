"""Historical Volatility = std of log returns × sqrt(annualization). For intraday bars use 252×N proxy."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "historical_volatility"; WEIGHT_DEFAULT = 0.5
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    log_ret = np.log(df["c"] / df["c"].shift())
    hv = log_ret.rolling(20).std() * math.sqrt(252) * 100
    last = float(hv.iloc[-1])
    payload = {"hv_pct_annualized": round(last, 2)}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class HistoricalVolatilityIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
