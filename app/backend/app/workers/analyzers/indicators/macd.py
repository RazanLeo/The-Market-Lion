"""MACD: fast EMA(12) - slow EMA(26); Signal = EMA(9) of MACD; Histogram = MACD - Signal."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "macd"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ema12 = df["c"].ewm(span=12, adjust=False).mean()
    ema26 = df["c"].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    sig = macd.ewm(span=9, adjust=False).mean()
    hist = macd - sig
    m, s, h = float(macd.iloc[-1]), float(sig.iloc[-1]), float(hist.iloc[-1])
    mp, sp = float(macd.iloc[-2]), float(sig.iloc[-2])
    cross_up = mp <= sp and m > s
    cross_dn = mp >= sp and m < s
    payload = {"macd": round(m, 5), "signal": round(s, 5), "histogram": round(h, 5),
               "cross_up": cross_up, "cross_down": cross_dn, "above_zero": m > 0}
    if cross_up: return AnalyzerResult(CODE, "buy", 75 if m > 0 else 60, WEIGHT_DEFAULT, payload)
    if cross_dn: return AnalyzerResult(CODE, "sell", 75 if m < 0 else 60, WEIGHT_DEFAULT, payload)
    if h > 0 and m > 0: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    if h < 0 and m < 0: return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class MacdIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
