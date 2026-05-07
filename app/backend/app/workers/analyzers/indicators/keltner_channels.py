"""Keltner Channels: EMA20 ± 2×ATR(20)."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "keltner_channels"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(20).mean()
    mid = c.ewm(span=20, adjust=False).mean()
    upper = mid + 2 * atr; lower = mid - 2 * atr
    last = float(c.iloc[-1])
    payload = {"kc_upper": round(float(upper.iloc[-1]), 5),
               "kc_mid": round(float(mid.iloc[-1]), 5),
               "kc_lower": round(float(lower.iloc[-1]), 5)}
    if last > float(upper.iloc[-1]): return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if last < float(lower.iloc[-1]): return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class KeltnerChannelsIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
