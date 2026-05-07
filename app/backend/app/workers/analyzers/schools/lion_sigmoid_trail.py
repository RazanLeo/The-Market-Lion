"""Lion Sigmoid Trail — sigmoid-shaped trailing stop that tightens as momentum slows.

Distance = ATR × sigmoid_factor; sigmoid_factor = 0.5 + tanh(slope × k) / 2
where slope is the EMA20 normalized slope. Returns suggested SL price.
"""
from __future__ import annotations
import math
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_sigmoid_trail"
WEIGHT_DEFAULT = 0.5


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ema20 = df["c"].ewm(span=20, adjust=False).mean()
    slope = float(ema20.iloc[-1] - ema20.iloc[-10]) / max(ema20.iloc[-10], 1e-9) * 100
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1] or 1)
    # Tighter when slope flat → sigmoid factor ~0.5; wider when slope strong → up to ~3
    f = 0.5 + math.tanh(slope * 0.3) * 1.25 + 1.0
    last = float(c.iloc[-1])
    suggested_long_sl = last - atr * f
    suggested_short_sl = last + atr * f
    payload = {"slope_pct": round(slope, 3), "atr": round(atr, 5),
               "factor": round(f, 3),
               "suggested_long_sl": round(suggested_long_sl, 5),
               "suggested_short_sl": round(suggested_short_sl, 5)}
    # This school is informational, weight is low and direction depends on context
    if slope > 1: return AnalyzerResult(CODE, "buy", 35, WEIGHT_DEFAULT, payload)
    if slope < -1: return AnalyzerResult(CODE, "sell", 35, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionSigmoidTrailAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
