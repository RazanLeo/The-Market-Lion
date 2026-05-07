"""Aroon Up = 100×(n - bars_since_max)/n; Aroon Down = 100×(n - bars_since_min)/n."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "aroon"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 25
    if len(df) < n + 5: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win_h = df["h"].iloc[-n:]; win_l = df["l"].iloc[-n:]
    bars_since_max = (n - 1) - int(win_h.argmax())
    bars_since_min = (n - 1) - int(win_l.argmin())
    aroon_up = 100 * (n - bars_since_max) / n
    aroon_dn = 100 * (n - bars_since_min) / n
    payload = {"aroon_up": round(aroon_up, 1), "aroon_down": round(aroon_dn, 1)}
    if aroon_up > 70 and aroon_dn < 30: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if aroon_dn > 70 and aroon_up < 30: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class AroonIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
