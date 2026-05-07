"""BB Bandwidth = (upper - lower) / mid. Squeeze when bandwidth is at low percentile."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "bollinger_bandwidth"; WEIGHT_DEFAULT = 0.6
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    sma = df["c"].rolling(20).mean(); sd = df["c"].rolling(20).std()
    bw = ((sma + 2 * sd) - (sma - 2 * sd)) / sma
    last = float(bw.iloc[-1])
    win = bw.iloc[-100:].dropna() if len(bw) >= 100 else bw.dropna()
    pct = float((win <= last).sum() / max(len(win), 1)) if len(win) else 0.5
    payload = {"bandwidth": round(last, 4), "percentile": round(pct, 2)}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class BollingerBandwidthIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
