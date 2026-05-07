"""Percentage Price Oscillator (PPO) = 100 × (EMA12 - EMA26) / EMA26."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "price_oscillator"; WEIGHT_DEFAULT = 0.85
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    e12 = df["c"].ewm(span=12, adjust=False).mean()
    e26 = df["c"].ewm(span=26, adjust=False).mean()
    ppo = 100 * (e12 - e26) / e26.replace(0, 1e-9)
    sig = ppo.ewm(span=9, adjust=False).mean()
    P, S = float(ppo.iloc[-1]), float(sig.iloc[-1])
    Pp, Sp = float(ppo.iloc[-2]), float(sig.iloc[-2])
    cross_up = Pp <= Sp and P > S; cross_dn = Pp >= Sp and P < S
    payload = {"ppo": round(P, 3), "signal": round(S, 3)}
    if cross_up: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if cross_dn: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class PriceOscillatorIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
