"""NVI: starts at 1000. If V < V[-1], NVI updates by % price change; else unchanged."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "negative_volume_index"; WEIGHT_DEFAULT = 0.6
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pct = df["c"].pct_change().fillna(0)
    v_dec = df["v"] < df["v"].shift()
    nvi = pd.Series(index=df.index, dtype=float); nvi.iloc[0] = 1000
    for i in range(1, len(df)):
        nvi.iloc[i] = nvi.iloc[i - 1] * (1 + (pct.iloc[i] if v_dec.iloc[i] else 0))
    sma_nvi = nvi.rolling(255).mean() if len(nvi) >= 255 else nvi.expanding().mean()
    last = float(nvi.iloc[-1]); avg = float(sma_nvi.iloc[-1])
    payload = {"nvi": round(last, 2), "nvi_avg": round(avg, 2)}
    if last > avg: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
class NegativeVolumeIndexIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
