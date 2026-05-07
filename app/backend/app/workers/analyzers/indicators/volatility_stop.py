"""Volatility Stop — ATR-based trailing stop. Long: stop = highest_close(N) - K×ATR(N)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "volatility_stop"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    n = 14; k = 3
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(n).mean()
    hh = c.rolling(n).max(); ll = c.rolling(n).min()
    long_stop = hh - k * atr; short_stop = ll + k * atr
    last_c = float(c.iloc[-1])
    ls = float(long_stop.iloc[-1]); ss = float(short_stop.iloc[-1])
    payload = {"long_stop": round(ls, 5), "short_stop": round(ss, 5)}
    if last_c > ls and last_c > float(c.iloc[-10]):
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if last_c < ss and last_c < float(c.iloc[-10]):
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class VolatilityStopIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
