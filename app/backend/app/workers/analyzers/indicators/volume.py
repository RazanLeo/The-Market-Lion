"""Raw volume + z-score over last 50 bars."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "volume"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    v = df["v"].fillna(0)
    z = (v - v.rolling(50).mean()) / v.rolling(50).std().replace(0, 1e-9)
    last_z = float(z.iloc[-1])
    direction_up = float(df["c"].iloc[-1]) > float(df["o"].iloc[-1])
    payload = {"vol_z": round(last_z, 2), "bar_up": direction_up}
    if last_z > 2 and direction_up: return AnalyzerResult(CODE, "buy", min(70.0, 40 + last_z * 8), WEIGHT_DEFAULT, payload)
    if last_z > 2 and not direction_up: return AnalyzerResult(CODE, "sell", min(70.0, 40 + last_z * 8), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class VolumeIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
