"""Ultimate Oscillator (Larry Williams) — weighted (4,2,1) over 7,14,28 periods."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "ultimate_oscillator"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 35: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    bp = c - pd.concat([l, c.shift()], axis=1).min(axis=1)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    avg7 = bp.rolling(7).sum() / tr.rolling(7).sum().replace(0, 1e-9)
    avg14 = bp.rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)
    avg28 = bp.rolling(28).sum() / tr.rolling(28).sum().replace(0, 1e-9)
    uo = 100 * (4 * avg7 + 2 * avg14 + avg28) / 7
    last = float(uo.iloc[-1])
    payload = {"uo": round(last, 1)}
    if last < 30: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if last > 70: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class UltimateOscillatorIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
