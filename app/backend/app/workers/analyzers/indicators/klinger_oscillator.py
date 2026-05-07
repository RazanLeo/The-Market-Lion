"""Klinger Volume Oscillator — EMA(34) - EMA(55) of Volume Force."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "klinger_oscillator"; WEIGHT_DEFAULT = 0.7
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 70 or "v" not in df.columns: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    hlc = (df["h"] + df["l"] + df["c"]) / 3
    trend = np.sign(hlc.diff().fillna(0))
    vf = trend * df["v"].fillna(0)
    ko = vf.ewm(span=34, adjust=False).mean() - vf.ewm(span=55, adjust=False).mean()
    sig = ko.ewm(span=13, adjust=False).mean()
    K, S = float(ko.iloc[-1]), float(sig.iloc[-1])
    Kp, Sp = float(ko.iloc[-2]), float(sig.iloc[-2])
    payload = {"klinger": round(K, 2), "signal": round(S, 2)}
    if Kp <= Sp and K > S: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if Kp >= Sp and K < S: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class KlingerOscillatorIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
