"""Money Flow Index (Wilder/Quong) = 100 - 100/(1 + MFR). MFR = +flow / -flow."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "mfi"; WEIGHT_DEFAULT = 0.9
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    tp = (df["h"] + df["l"] + df["c"]) / 3
    mf = tp * df["v"].fillna(0)
    pos = mf.where(tp > tp.shift(), 0).rolling(14).sum()
    neg = mf.where(tp < tp.shift(), 0).rolling(14).sum().replace(0, 1e-9)
    mfi = 100 - 100 / (1 + pos / neg)
    last = float(mfi.iloc[-1])
    payload = {"mfi": round(last, 1)}
    if last < 20: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last > 80: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class MfiIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
