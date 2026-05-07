"""Footprint / Delta — per-bar bid/ask volume estimate + imbalance + stacked imbalance.

Without raw bid/ask we estimate:
  ask_vol = volume × close-position-in-bar (close near high → mostly ask-hits = buying)
  bid_vol = volume × (1 - close-position-in-bar)
Imbalance per bar = abs(ask_vol - bid_vol) / total
Stacked = 3 consecutive bars all showing same-side imbalance > 0.55.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "footprint_delta"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    pos = (df["c"] - df["l"]) / rng
    v = df["v"].fillna(0)
    ask = v * pos; bid = v * (1 - pos)
    delta = ask - bid
    last_n = 5
    imb = (ask - bid).abs() / (ask + bid).replace(0, 1e-9)
    last_imb = float(imb.iloc[-1])
    # Stacked imbalance
    stacked_buy = all((delta.iloc[i] > 0 and imb.iloc[i] > 0.55) for i in range(-3, 0))
    stacked_sell = all((delta.iloc[i] < 0 and imb.iloc[i] > 0.55) for i in range(-3, 0))
    cum_delta = float(delta.iloc[-last_n:].sum())
    payload = {"last_imbalance": round(last_imb, 3),
               "cum_delta_5bars": round(cum_delta, 2),
               "stacked_buy_imbalance": stacked_buy,
               "stacked_sell_imbalance": stacked_sell}
    if stacked_buy: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if stacked_sell: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if cum_delta > 0 and last_imb > 0.6: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if cum_delta < 0 and last_imb > 0.6: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FootprintDeltaAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
