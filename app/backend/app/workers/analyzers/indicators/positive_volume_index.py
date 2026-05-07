"""PVI: opposite of NVI. Updates only when V > V[-1]."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "positive_volume_index"; WEIGHT_DEFAULT = 0.6
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pct = df["c"].pct_change().fillna(0)
    v_inc = df["v"] > df["v"].shift()
    pvi = pd.Series(index=df.index, dtype=float); pvi.iloc[0] = 1000
    for i in range(1, len(df)):
        pvi.iloc[i] = pvi.iloc[i - 1] * (1 + (pct.iloc[i] if v_inc.iloc[i] else 0))
    sma_pvi = pvi.rolling(255).mean() if len(pvi) >= 255 else pvi.expanding().mean()
    last = float(pvi.iloc[-1]); avg = float(sma_pvi.iloc[-1])
    payload = {"pvi": round(last, 2), "pvi_avg": round(avg, 2)}
    if last > avg: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
class PositiveVolumeIndexIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
