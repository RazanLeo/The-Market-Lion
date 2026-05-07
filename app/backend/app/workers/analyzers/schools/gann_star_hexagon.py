"""Gann Star / Hexagon Chart — square-of-six progression: sqrt(price) × 60° increments.

Each hex step adds (60/360) × 2π rotation to sqrt(price). Equivalent prices = (sqrt(p) + k×0.5)^2.
We build levels around the most-recent significant pivot and detect price hitting one.
"""
from __future__ import annotations
import math
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "gann_star_hexagon"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-60:]
    pivot = float(win["l"].min()) if int(win["l"].argmin()) > int(win["h"].argmax()) else float(win["h"].max())
    base = math.sqrt(pivot)
    # 60° hex steps: 1/6 of a full sqrt-rotation; commonly 0.1667 increments
    steps = []
    for k in range(1, 13):
        up = (base + k * (1 / 6.0)) ** 2
        dn = (base - k * (1 / 6.0)) ** 2 if base - k * (1 / 6.0) > 0 else None
        steps.append(("hex+" + str(k), up))
        if dn: steps.append(("hex-" + str(k), dn))
    last = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    nearest = min(steps, key=lambda kv: abs(kv[1] - last))
    in_zone = abs(nearest[1] - last) < atr * 0.3
    payload = {"pivot": round(pivot, 5), "nearest_level": nearest[0],
               "nearest_price": round(nearest[1], 5), "in_zone": in_zone}
    if not in_zone:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    direction_up = float(df["c"].iloc[-1]) > float(df["c"].iloc[-5])
    if "hex-" in nearest[0] and not direction_up:
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if "hex+" in nearest[0] and direction_up:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class GannStarHexagonAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
