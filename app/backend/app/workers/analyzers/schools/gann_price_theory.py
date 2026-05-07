"""Gann Price Theory — percentage retracements at 25, 37.5, 50, 62.5, 75, 87.5%.

These are Gann's price-percentage levels (different from Fibonacci): 1/8 increments of the leg.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "gann_price_theory"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-50:]
    swing_h = float(win["h"].max()); swing_l = float(win["l"].min())
    rng = swing_h - swing_l
    if rng <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    direction_up = int(win["h"].argmax()) > int(win["l"].argmin())
    levels_pct = [0.25, 0.375, 0.50, 0.625, 0.75, 0.875]
    if direction_up:
        levels = {f"{int(p*1000)/10}%": swing_h - p * rng for p in levels_pct}
    else:
        levels = {f"{int(p*1000)/10}%": swing_l + p * rng for p in levels_pct}
    last = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    nearest = min(levels.items(), key=lambda kv: abs(kv[1] - last))
    in_zone = abs(nearest[1] - last) < atr * 0.3
    payload = {"direction": "up" if direction_up else "down",
               "swing_high": round(swing_h, 5), "swing_low": round(swing_l, 5),
               "gann_levels": {k: round(v, 5) for k, v in levels.items()},
               "nearest_level": nearest[0], "nearest_price": round(nearest[1], 5),
               "in_zone": in_zone}
    if not in_zone:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    pct = float(nearest[0].rstrip("%")) / 100
    if direction_up and pct in (0.50, 0.625):
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if (not direction_up) and pct in (0.50, 0.625):
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if direction_up: return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)


class GannPriceTheoryAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
