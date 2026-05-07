"""Lucas Series Levels — alternative to Fibonacci using Lucas number ratios (1.236, 1.382, 1.500).

Compute retracement of the most recent swing using Lucas-derived ratios (sums/differences of
adjacent Lucas numbers normalized): primary levels 0.236, 0.382, 0.500, 0.618 (overlap with Fib),
and Lucas-only 0.764, 0.854, 0.917 (derived from Lucas convergents).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lucas_series_school"
WEIGHT_DEFAULT = 0.7


LUCAS_LEVELS = [0.236, 0.382, 0.500, 0.618, 0.764, 0.854, 0.917]


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-50:]
    swing_h = float(win["h"].max()); swing_l = float(win["l"].min())
    rng = swing_h - swing_l
    if rng == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    direction_up = int(win["h"].argmax()) > int(win["l"].argmin())
    if direction_up:
        levels = {f"{int(p*1000)/10}%": swing_h - p * rng for p in LUCAS_LEVELS}
    else:
        levels = {f"{int(p*1000)/10}%": swing_l + p * rng for p in LUCAS_LEVELS}

    last = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    nearest = min(levels.items(), key=lambda kv: abs(kv[1] - last))
    in_zone = abs(nearest[1] - last) < atr * 0.3

    payload = {"direction": "up_leg" if direction_up else "down_leg",
               "swing_high": round(swing_h, 5), "swing_low": round(swing_l, 5),
               "lucas_levels": {k: round(v, 5) for k, v in levels.items()},
               "nearest_level": nearest[0], "nearest_price": round(nearest[1], 5),
               "in_zone": in_zone}
    if not in_zone:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    pct = float(nearest[0].rstrip("%")) / 100
    if direction_up and 0.45 <= pct <= 0.92:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if (not direction_up) and 0.45 <= pct <= 0.92:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 25, WEIGHT_DEFAULT, payload)


class LucasSeriesSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
