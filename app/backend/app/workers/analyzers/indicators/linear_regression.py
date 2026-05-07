"""Linear Regression line (period 50). Slope > 0 = uptrend; channel ±2σ from residuals."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "linear_regression"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 50
    if len(df) < n: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    y = df["c"].iloc[-n:].to_numpy(); x = np.arange(n)
    slope, intercept = np.polyfit(x, y, 1)
    fit = slope * x + intercept
    residuals = y - fit
    sigma = float(residuals.std()); last_fit = float(fit[-1])
    upper = last_fit + 2 * sigma; lower = last_fit - 2 * sigma
    last = float(df["c"].iloc[-1])
    payload = {"slope_per_bar": round(float(slope), 6),
               "fit_now": round(last_fit, 5),
               "upper_2sigma": round(upper, 5), "lower_2sigma": round(lower, 5)}
    if last < lower: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last > upper: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if slope > 0 and last > last_fit: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if slope < 0 and last < last_fit: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class LinearRegressionIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
