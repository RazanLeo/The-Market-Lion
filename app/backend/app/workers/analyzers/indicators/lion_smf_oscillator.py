"""Lion Smart Money Flow (SMF) — vol-weighted close oscillator.

SMF = Σ(close × volume × position) / Σ(volume) over rolling 30, where
position = (close - low) / (high - low) (1 = strong close, 0 = weak close).
Above 0.6 = smart money buying; below 0.4 = smart money selling.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_smf_oscillator"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    pos = (df["c"] - df["l"]) / rng
    weighted = pos * df["v"]
    smf = weighted.rolling(30).sum() / df["v"].rolling(30).sum().replace(0, 1e-9)
    last = float(smf.iloc[-1])
    prev = float(smf.iloc[-2])
    payload = {"smf": round(last, 3), "smf_prev": round(prev, 3),
               "bias": "smart_buying" if last > 0.6 else "smart_selling" if last < 0.4 else "neutral"}
    if last > 0.65 and last > prev:
        return AnalyzerResult(CODE, "buy", min(80, 50 + (last - 0.5) * 100), WEIGHT_DEFAULT, payload)
    if last < 0.35 and last < prev:
        return AnalyzerResult(CODE, "sell", min(80, 50 + (0.5 - last) * 100), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionSmfOscillatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
