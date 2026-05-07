"""Auto Trend Lines — least-squares regression line as dynamic trend.

Fits a linear regression to the last N closes, computes slope (price/bar) and r².
Bullish trend = positive slope with r² > 0.5. Channel boundaries = ±2σ from regression.
Buy when price tests lower channel from above in an uptrend.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "auto_trend_lines_ind"
WEIGHT_DEFAULT = 0.9


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df["c"].iloc[-50:].to_numpy()
    x = np.arange(len(win), dtype=float)
    slope, intercept = np.polyfit(x, win, 1)
    fit = slope * x + intercept
    resid = win - fit
    sigma = float(np.std(resid))
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((win - win.mean()) ** 2)) + 1e-9
    r2 = 1 - ss_res / ss_tot
    last_c = float(win[-1])
    upper = float(fit[-1] + 2 * sigma); lower = float(fit[-1] - 2 * sigma)
    payload = {"slope": round(float(slope), 6), "r2": round(r2, 3),
               "regression": round(float(fit[-1]), 5), "upper_ch": round(upper, 5),
               "lower_ch": round(lower, 5), "sigma": round(sigma, 5)}
    if slope > 0 and r2 > 0.5 and last_c < float(fit[-1]) - sigma:
        return AnalyzerResult(CODE, "buy", min(80, 50 + r2 * 40), WEIGHT_DEFAULT, payload)
    if slope < 0 and r2 > 0.5 and last_c > float(fit[-1]) + sigma:
        return AnalyzerResult(CODE, "sell", min(80, 50 + r2 * 40), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AutoTrendLinesIndAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
