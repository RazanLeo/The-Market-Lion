"""Wilder ATR(14). True Range = max(H-L, |H-C[-1]|, |L-C[-1]|); ATR = EMA(TR) with α=1/14."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "atr"; WEIGHT_DEFAULT = 0.5
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    last = float(atr.iloc[-1])
    avg = float(atr.iloc[-50:].mean()) if len(atr) >= 50 else last
    payload = {"atr14": round(last, 5), "regime_x_avg": round(last / max(avg, 1e-9), 2)}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)  # ATR is volatility, no direction
class AtrIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
