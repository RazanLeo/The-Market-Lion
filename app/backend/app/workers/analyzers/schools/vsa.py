"""VSA — Volume Spread Analysis (Tom Williams).

Detects key VSA bars:
  • No-Demand: up bar with narrow range and low volume → bearish
  • No-Supply: down bar with narrow range and low volume → bullish
  • Stopping Volume: high vol + narrow spread + lower wick at swing low → bullish
  • Climactic Volume: very high vol + wide spread = climax (often reversal)
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "vsa"
WEIGHT_DEFAULT = 1.0


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = _atr(df)
    atr_now = float(atr.iloc[-1] or 0)
    vol_avg = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    if atr_now <= 0 or vol_avg <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o = float(df["o"].iloc[-1]); c = float(df["c"].iloc[-1])
    h = float(df["h"].iloc[-1]); l = float(df["l"].iloc[-1])
    v = float(df["v"].iloc[-1])
    rng = h - l
    body = abs(c - o); is_bull = c > o
    narrow = rng < atr_now * 0.6; wide = rng > atr_now * 1.5
    low_v = v < vol_avg * 0.7; high_v = v > vol_avg * 1.5; climax_v = v > vol_avg * 2.5
    swing_low = float(df["l"].iloc[-20:].min())
    near_low = abs(l - swing_low) < atr_now * 0.5
    no_demand = is_bull and narrow and low_v
    no_supply = (not is_bull) and narrow and low_v
    stopping_vol = near_low and narrow and high_v and (min(o, c) - l) > body * 1.5
    climax = wide and climax_v
    payload = {"no_demand": no_demand, "no_supply": no_supply,
               "stopping_volume": stopping_vol, "climax": climax,
               "vol_ratio": round(v / vol_avg, 2)}
    if stopping_vol or no_supply:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if no_demand:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if climax and is_bull:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if climax and not is_bull:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VsaAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
