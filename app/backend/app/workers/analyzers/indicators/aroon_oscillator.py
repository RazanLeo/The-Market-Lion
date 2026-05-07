"""Aroon Oscillator = Aroon Up - Aroon Down. Range -100..+100."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "aroon_oscillator"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 25
    if len(df) < n + 5: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win_h = df["h"].iloc[-n:]; win_l = df["l"].iloc[-n:]
    bars_since_max = (n - 1) - int(win_h.argmax())
    bars_since_min = (n - 1) - int(win_l.argmin())
    aup = 100 * (n - bars_since_max) / n
    adn = 100 * (n - bars_since_min) / n
    osc = aup - adn
    payload = {"aroon_osc": round(osc, 1)}
    if osc > 50: return AnalyzerResult(CODE, "buy", min(70.0, 40 + osc * 0.4), WEIGHT_DEFAULT, payload)
    if osc < -50: return AnalyzerResult(CODE, "sell", min(70.0, 40 + abs(osc) * 0.4), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class AroonOscillatorIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
