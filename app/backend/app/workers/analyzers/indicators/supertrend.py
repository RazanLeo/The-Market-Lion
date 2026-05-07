"""Supertrend (factor=3, ATR period=10). Final upper / lower bands trail price."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "supertrend"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(10).mean()
    hl2 = (h + l) / 2
    f_up = hl2 + 3 * atr; f_dn = hl2 - 3 * atr
    upper = f_up.copy(); lower = f_dn.copy()
    for i in range(1, len(df)):
        if not pd.isna(upper.iloc[i - 1]):
            upper.iloc[i] = f_up.iloc[i] if (f_up.iloc[i] < upper.iloc[i - 1] or c.iloc[i - 1] > upper.iloc[i - 1]) else upper.iloc[i - 1]
            lower.iloc[i] = f_dn.iloc[i] if (f_dn.iloc[i] > lower.iloc[i - 1] or c.iloc[i - 1] < lower.iloc[i - 1]) else lower.iloc[i - 1]
    last_c = float(c.iloc[-1]); u = float(upper.iloc[-1]); lo = float(lower.iloc[-1])
    side = "up" if last_c > u else "down" if last_c < lo else "transition"
    payload = {"upper": round(u, 5), "lower": round(lo, 5), "side": side}
    if last_c > u: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if last_c < lo: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class SupertrendIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
