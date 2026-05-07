"""A/D Line. Cumulative sum of MFV (money flow volume)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "accumulation_distribution"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    mfm = ((df["c"] - df["l"]) - (df["h"] - df["c"])) / (df["h"] - df["l"]).replace(0, 1e-9)
    ad = (mfm * df["v"].fillna(0)).cumsum()
    last = float(ad.iloc[-1]); prev = float(ad.iloc[-30])
    rising = last > prev
    p_change = float(df["c"].iloc[-1] - df["c"].iloc[-30])
    div_bull = p_change < 0 and rising
    div_bear = p_change > 0 and not rising
    payload = {"ad": round(last, 2), "rising_30": rising,
               "bull_div": div_bull, "bear_div": div_bear}
    if div_bull: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if div_bear: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if rising: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
class AccumulationDistributionIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
