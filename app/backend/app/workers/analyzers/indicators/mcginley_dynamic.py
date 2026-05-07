"""McGinley Dynamic. M[i] = M[i-1] + (P - M[i-1]) / (k×N×(P/M[i-1])^4)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "mcginley_dynamic"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 14; k = 0.6
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    m = pd.Series(index=df.index, dtype=float)
    m.iloc[0] = float(df["c"].iloc[0])
    for i in range(1, len(df)):
        prev = float(m.iloc[i - 1]) or 1e-9
        p = float(df["c"].iloc[i])
        m.iloc[i] = prev + (p - prev) / (k * n * (p / prev) ** 4)
    v = float(m.iloc[-1]); vp = float(m.iloc[-5])
    slope = (v - vp) / vp * 100 if vp else 0
    last = float(df["c"].iloc[-1])
    payload = {"mcginley": round(v, 5), "slope_pct": round(slope, 3)}
    if last > v and slope > 0: return AnalyzerResult(CODE, "buy", min(70.0, 40 + slope * 6), WEIGHT_DEFAULT, payload)
    if last < v and slope < 0: return AnalyzerResult(CODE, "sell", min(70.0, 40 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class McginleyDynamicIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
