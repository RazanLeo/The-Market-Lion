"""VIX proxy via realized vol of log-returns × 100×sqrt(N). For single instrument."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "volatility_index_proxy"; WEIGHT_DEFAULT = 0.5
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    log_ret = np.log(df["c"] / df["c"].shift())
    rv = float(log_ret.rolling(20).std().iloc[-1] * math.sqrt(252) * 100)
    payload = {"vix_proxy_pct_annualized": round(rv, 2)}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class VolatilityIndexProxyIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
