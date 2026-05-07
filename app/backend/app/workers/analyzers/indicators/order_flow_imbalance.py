"""Order Flow Imbalance (OFI) — bid-ask volume ratio proxy.

True OFI requires L2 data; here we proxy with intra-bar buy/sell estimation:
  buy_vol  = v × (c-l) / (h-l)
  sell_vol = v × (h-c) / (h-l)
OFI = (buy - sell) / (buy + sell) over rolling 10-bar window. Persistent OFI > +0.3
or < -0.3 signals strong directional pressure.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "order_flow_imbalance"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    pos = (df["c"] - df["l"]) / rng
    buy_vol = df["v"] * pos
    sell_vol = df["v"] * (1 - pos)
    bv_10 = buy_vol.rolling(10).sum()
    sv_10 = sell_vol.rolling(10).sum()
    ofi = (bv_10 - sv_10) / (bv_10 + sv_10 + 1e-9)
    last = float(ofi.iloc[-1])
    prev = float(ofi.iloc[-2])
    streak = 0
    for v in ofi.iloc[-5:][::-1]:
        if (v > 0.1 and last > 0) or (v < -0.1 and last < 0):
            streak += 1
        else:
            break
    payload = {"ofi_10b": round(last, 3), "prev": round(prev, 3),
               "persistence_streak": streak}
    if last > 0.3 and streak >= 3:
        return AnalyzerResult(CODE, "buy", min(80, 50 + last * 80), WEIGHT_DEFAULT, payload)
    if last < -0.3 and streak >= 3:
        return AnalyzerResult(CODE, "sell", min(80, 50 + abs(last) * 80), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class OrderFlowImbalanceAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
