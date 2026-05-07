"""Force Index (Elder): EMA(13) of (close[i] - close[i-1]) × volume."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "force_index"; WEIGHT_DEFAULT = 0.75
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    fi = ((df["c"] - df["c"].shift()) * df["v"].fillna(0)).ewm(span=13, adjust=False).mean()
    last = float(fi.iloc[-1]); prev = float(fi.iloc[-2])
    payload = {"force_index": round(last, 2)}
    if last > 0 and prev <= 0: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last < 0 and prev >= 0: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if last > 0: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
class ForceIndexIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
