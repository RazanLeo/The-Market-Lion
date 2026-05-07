"""Kaufman Adaptive MA. ER = |C-C[n]|/Σ|ΔC|; SC = (ER×(fast-slow) + slow)^2; KAMA = KAMA[-1] + SC×(C-KAMA[-1])."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult
CODE = "kama"; WEIGHT_DEFAULT = 1.0
def analyze(df: pd.DataFrame) -> AnalyzerResult:
    n = 10; fast = 2 / (2 + 1); slow = 2 / (30 + 1)
    if len(df) < 50: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"].astype(float)
    chg = c.diff(n).abs()
    vol = c.diff().abs().rolling(n).sum().replace(0, 1e-9)
    er = chg / vol
    sc = ((er * (fast - slow) + slow) ** 2).fillna(slow ** 2)
    kama = pd.Series(index=df.index, dtype=float)
    kama.iloc[n] = float(c.iloc[n])
    for i in range(n + 1, len(df)):
        kama.iloc[i] = float(kama.iloc[i - 1]) + float(sc.iloc[i]) * (float(c.iloc[i]) - float(kama.iloc[i - 1]))
    v = float(kama.iloc[-1]); vp = float(kama.iloc[-5])
    slope = (v - vp) / vp * 100 if vp else 0
    last = float(c.iloc[-1])
    payload = {"kama": round(v, 5), "ER": round(float(er.iloc[-1]), 3), "slope_pct": round(slope, 3)}
    if last > v and slope > 0: return AnalyzerResult(CODE, "buy", min(75.0, 45 + slope * 6), WEIGHT_DEFAULT, payload)
    if last < v and slope < 0: return AnalyzerResult(CODE, "sell", min(75.0, 45 + abs(slope) * 6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
class KamaIndicator:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
