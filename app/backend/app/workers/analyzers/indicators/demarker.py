"""DeMarker(14): SMA(de_max,14)/(SMA(de_max)+SMA(de_min)). de_max = max(0, h-h[-1]); de_min = max(0, l[-1]-l)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "demarker"; WEIGHT_DEFAULT = 0.8
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    de_max = (df["h"] - df["h"].shift()).clip(lower=0)
    de_min = (df["l"].shift() - df["l"]).clip(lower=0)
    sm = de_max.rolling(14).mean()
    smin = de_min.rolling(14).mean()
    dem = sm / (sm + smin + 1e-9)
    last = float(dem.iloc[-1])
    payload = {"demarker": round(last, 3)}
    if last < 0.3: return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if last > 0.7: return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class DemarkerIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
