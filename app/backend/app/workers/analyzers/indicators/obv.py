"""On-Balance Volume. OBV[i] = OBV[i-1] + sign(C-C[-1]) × V."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "obv"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sgn = np.sign(df["c"].diff().fillna(0))
    obv = (sgn * df["v"].fillna(0)).cumsum()
    last = float(obv.iloc[-1]); prev = float(obv.iloc[-30])
    rising = last > prev
    # Divergence: price down but OBV up → bullish
    p_change = float(df["c"].iloc[-1] - df["c"].iloc[-30])
    div_bull = p_change < 0 and rising
    div_bear = p_change > 0 and not rising
    payload = {"obv": round(last, 2), "rising_30bars": rising,
               "bull_divergence": div_bull, "bear_divergence": div_bear}
    if div_bull: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if div_bear: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if rising: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
class ObvIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
