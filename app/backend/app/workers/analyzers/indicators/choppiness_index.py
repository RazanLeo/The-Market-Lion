"""Choppiness Index = 100 × log10(ΣTR_n / (Hn-Ln)) / log10(n). >61.8 = choppy; <38.2 = trending."""
from __future__ import annotations
import math
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "choppiness_index"; WEIGHT_DEFAULT = 0.6
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 14
    if len(df) < n + 5: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    sum_tr = tr.rolling(n).sum()
    hh = h.rolling(n).max(); ll = l.rolling(n).min()
    rng = (hh - ll).replace(0, 1e-9)
    ci = 100 * (sum_tr / rng).apply(lambda x: math.log10(x) if x > 0 else 0) / math.log10(n)
    last = float(ci.iloc[-1])
    payload = {"chop": round(last, 1), "regime": "choppy" if last > 61.8 else "trending" if last < 38.2 else "neutral"}
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class ChoppinessIndexIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
