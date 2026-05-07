"""Williams Fractals — 5-bar fractal where middle is the max (up-fractal / resistance) or min (down-fractal / support).
Latest broken fractal = directional signal.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fractal_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    up_fractals = []; dn_fractals = []
    for i in range(2, len(df) - 2):
        if (df["h"].iloc[i] > df["h"].iloc[i - 1] and df["h"].iloc[i] > df["h"].iloc[i - 2]
                and df["h"].iloc[i] > df["h"].iloc[i + 1] and df["h"].iloc[i] > df["h"].iloc[i + 2]):
            up_fractals.append((i, float(df["h"].iloc[i])))
        if (df["l"].iloc[i] < df["l"].iloc[i - 1] and df["l"].iloc[i] < df["l"].iloc[i - 2]
                and df["l"].iloc[i] < df["l"].iloc[i + 1] and df["l"].iloc[i] < df["l"].iloc[i + 2]):
            dn_fractals.append((i, float(df["l"].iloc[i])))
    last_close = float(df["c"].iloc[-1])

    most_recent_up = up_fractals[-1] if up_fractals else None
    most_recent_dn = dn_fractals[-1] if dn_fractals else None
    broke_up = most_recent_up and last_close > most_recent_up[1]
    broke_dn = most_recent_dn and last_close < most_recent_dn[1]

    payload = {"up_fractals_count": len(up_fractals),
               "dn_fractals_count": len(dn_fractals),
               "most_recent_up": most_recent_up,
               "most_recent_dn": most_recent_dn,
               "broke_up_fractal": broke_up,
               "broke_dn_fractal": broke_dn}
    if broke_up: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if broke_dn: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FractalSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
