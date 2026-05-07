"""Mass Index = sum_25(EMA9(H-L) / EMA9(EMA9(H-L))). >27 = reversal warning."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "mass_index"; WEIGHT_DEFAULT = 0.6
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rng = (df["h"] - df["l"])
    ema9 = rng.ewm(span=9, adjust=False).mean()
    ema9d = ema9.ewm(span=9, adjust=False).mean()
    ratio = ema9 / ema9d.replace(0, 1e-9)
    mi = ratio.rolling(25).sum()
    last = float(mi.iloc[-1])
    payload = {"mass_index": round(last, 2), "reversal_warning": last > 27}
    if last > 27: return AnalyzerResult(CODE, "neutral", 50, WEIGHT_DEFAULT, payload)  # warning, no direction
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class MassIndexIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
