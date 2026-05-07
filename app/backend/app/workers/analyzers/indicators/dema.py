"""Double EMA: DEMA = 2×EMA - EMA(EMA). Reduces lag of single EMA."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "dema"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    e1 = df["c"].ewm(span=20, adjust=False).mean()
    e2 = e1.ewm(span=20, adjust=False).mean()
    dema = 2 * e1 - e2
    last = float(df["c"].iloc[-1]); v = float(dema.iloc[-1]); vp = float(dema.iloc[-5])
    slope = (v - vp) / vp * 100 if vp else 0
    payload = {"dema": round(v, 5), "slope_pct": round(slope, 3)}
    if last > v and slope > 0: return AnalyzerResult(CODE, "buy", min(75.0, 45 + slope * 6), WEIGHT_DEFAULT, payload)
    if last < v and slope < 0: return AnalyzerResult(CODE, "sell", min(75.0, 45 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class DemaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
