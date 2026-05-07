"""Volume-Weighted Moving Average: VWMA = Σ(price×volume) / Σ volume over n bars."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "vwma"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 20
    if len(df) < n + 5 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pv = df["c"] * df["v"].fillna(0)
    vwma = pv.rolling(n).sum() / df["v"].fillna(0).rolling(n).sum().replace(0, 1e-9)
    v = float(vwma.iloc[-1]); vp = float(vwma.iloc[-5])
    slope = (v - vp) / vp * 100 if vp else 0
    last = float(df["c"].iloc[-1])
    payload = {"vwma20": round(v, 5), "slope_pct": round(slope, 3)}
    if last > v and slope > 0: return AnalyzerResult(CODE, "buy", min(75.0, 45 + slope * 6), WEIGHT_DEFAULT, payload)
    if last < v and slope < 0: return AnalyzerResult(CODE, "sell", min(75.0, 45 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class VwmaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
