"""Volume Oscillator = (SMA(V,5) - SMA(V,20)) / SMA(V,20) × 100. >0 = volume rising."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "volume_oscillator"; WEIGHT_DEFAULT = 0.65
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    fast = df["v"].rolling(5).mean(); slow = df["v"].rolling(20).mean()
    vo = (fast - slow) / slow.replace(0, 1e-9) * 100
    last = float(vo.iloc[-1])
    direction_up = float(df["c"].iloc[-1]) > float(df["c"].iloc[-5])
    payload = {"vol_osc_pct": round(last, 1), "trend_up": direction_up}
    if last > 10 and direction_up: return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if last > 10 and not direction_up: return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class VolumeOscillatorIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
