"""Cumulative Delta Indicator — variant CVD using bar-position weighting.

Estimates buy/sell volume from where close is in the bar's range:
  buy_vol  = volume × (c-l)/(h-l)
  sell_vol = volume × (h-c)/(h-l)
delta = buy_vol - sell_vol; CD = cumulative delta. More accurate than sign-based CVD.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "cumulative_delta_indicator"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    pos = (df["c"] - df["l"]) / rng
    buy_vol = df["v"] * pos
    sell_vol = df["v"] * (1 - pos)
    delta = buy_vol - sell_vol
    cd = delta.cumsum()
    cd_now = float(cd.iloc[-1])
    cd_5 = float(cd.iloc[-5])
    cd_20 = float(cd.iloc[-20])
    short_change = cd_now - cd_5
    long_change = cd_now - cd_20
    last_5_buy = float(buy_vol.iloc[-5:].sum())
    last_5_sell = float(sell_vol.iloc[-5:].sum())
    imb_5 = (last_5_buy - last_5_sell) / (last_5_buy + last_5_sell + 1e-9)
    payload = {"cumulative_delta": round(cd_now, 2),
               "short_change_5b": round(short_change, 2),
               "long_change_20b": round(long_change, 2),
               "imbalance_5b": round(imb_5, 3)}
    if short_change > 0 and long_change > 0 and imb_5 > 0.15:
        return AnalyzerResult(CODE, "buy", min(80, 50 + abs(imb_5) * 100), WEIGHT_DEFAULT, payload)
    if short_change < 0 and long_change < 0 and imb_5 < -0.15:
        return AnalyzerResult(CODE, "sell", min(80, 50 + abs(imb_5) * 100), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CumulativeDeltaIndicatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
