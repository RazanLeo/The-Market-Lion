"""A/D Volume Line — same A/D Line but normalized by volume to compare across instruments."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "ad_volume_line"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    mfm = ((df["c"] - df["l"]) - (df["h"] - df["c"])) / (df["h"] - df["l"]).replace(0, 1e-9)
    mfv = mfm * df["v"].fillna(0)
    ad_norm = mfv / df["v"].fillna(0).replace(0, 1e-9)
    smoothed = ad_norm.cumsum() / df["v"].fillna(0).cumsum().replace(0, 1e-9)
    last = float(smoothed.iloc[-1])
    payload = {"ad_volume_line": round(last, 4)}
    if last > 0: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
class AdVolumeLineIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
