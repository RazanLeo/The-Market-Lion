"""Sacred Geometry — ratio levels at phi (1.618), sqrt(2)≈1.414, sqrt(3)≈1.732, 2π≈6.283 fractions.

For the most recent leg, project levels at:
  phi-retrace 1/phi = 0.618, 1/phi^2 = 0.382, sqrt(2)-1 = 0.414, sqrt(3)-1 = 0.732, 1/2π = 0.159
"""
from __future__ import annotations
import math
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "sacred_geometry"
WEIGHT_DEFAULT = 0.65

RATIOS = {
    "phi_inv":     1 / 1.618,        # 0.618
    "phi_inv_sq":  1 / 1.618 ** 2,   # 0.382
    "sqrt2_minus": math.sqrt(2) - 1, # 0.414
    "sqrt3_minus": math.sqrt(3) - 1, # 0.732
    "two_pi_inv":  1 / (2 * math.pi),# 0.159
    "phi_minus_1": 1.618 - 1,        # 0.618 (alt)
}


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-50:]
    swing_h = float(win["h"].max()); swing_l = float(win["l"].min())
    rng = swing_h - swing_l
    if rng <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    direction_up = int(win["h"].argmax()) > int(win["l"].argmin())
    if direction_up:
        levels = {k: swing_h - r * rng for k, r in RATIOS.items()}
    else:
        levels = {k: swing_l + r * rng for k, r in RATIOS.items()}
    last = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    nearest = min(levels.items(), key=lambda kv: abs(kv[1] - last))
    in_zone = abs(nearest[1] - last) < atr * 0.3
    payload = {"direction_up": direction_up,
               "levels": {k: round(v, 5) for k, v in levels.items()},
               "nearest_ratio": nearest[0], "nearest_price": round(nearest[1], 5),
               "in_zone": in_zone}
    if not in_zone:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    if direction_up:
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)


class SacredGeometryAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
