"""Footprint Chart — per-bar bid/ask volume split (estimated from candle position).

For each bar:
  ask_vol (buys) = v × (c - l) / (h - l)
  bid_vol (sells)= v × (h - c) / (h - l)
  delta = ask - bid
A "stacked imbalance" = consecutive bars with same-sign delta > 60% of bar volume.
3+ stacked imbalances indicate strong directional flow.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "footprint"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    pos = (df["c"] - df["l"]) / rng
    ask = df["v"] * pos
    bid = df["v"] * (1 - pos)
    delta = ask - bid
    delta_ratio = delta / df["v"].replace(0, 1e-9)
    last5 = delta_ratio.iloc[-5:]
    bull_imb = int((last5 > 0.6).sum())
    bear_imb = int((last5 < -0.6).sum())
    last_delta = float(delta.iloc[-1])
    payload = {"last_bar_delta": round(last_delta, 2),
               "bull_stacked_5b": bull_imb, "bear_stacked_5b": bear_imb,
               "delta_ratio_now": round(float(delta_ratio.iloc[-1]), 3)}
    if bull_imb >= 3:
        return AnalyzerResult(CODE, "buy", min(80, 55 + bull_imb * 7), WEIGHT_DEFAULT, payload)
    if bear_imb >= 3:
        return AnalyzerResult(CODE, "sell", min(80, 55 + bear_imb * 7), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FootprintAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
