"""CMF = Σ(((C-L)-(H-C))/(H-L) × V) / Σ V over 20 periods."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "chaikin_money_flow"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    mfm = ((df["c"] - df["l"]) - (df["h"] - df["c"])) / (df["h"] - df["l"]).replace(0, 1e-9)
    mfv = mfm * df["v"].fillna(0)
    cmf = mfv.rolling(20).sum() / df["v"].fillna(0).rolling(20).sum().replace(0, 1e-9)
    last = float(cmf.iloc[-1])
    payload = {"cmf": round(last, 3)}
    if last > 0.10: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last < -0.10: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class ChaikinMoneyFlowIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
