"""Japanese Candlesticks — multi-bar pattern recognition (Sakata-style).

Detects: Three Black Crows, Three White Soldiers, Morning Star, Evening Star,
Three Inside Up/Down. Uses 3-bar lookback and body/wick proportions.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "japanese_candlesticks"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 10:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o = df["o"].iloc[-3:].values; h = df["h"].iloc[-3:].values
    l = df["l"].iloc[-3:].values; c = df["c"].iloc[-3:].values
    bodies = [abs(c[i] - o[i]) for i in range(3)]
    bull = [c[i] > o[i] for i in range(3)]
    three_white = all(bull) and c[2] > c[1] > c[0] and o[2] > o[1] > o[0] and \
                  all(b > 0 for b in bodies)
    three_black = all(not b for b in bull) and c[2] < c[1] < c[0] and o[2] < o[1] < o[0] and \
                  all(b > 0 for b in bodies)
    # Morning Star: long red, small body, long green
    morn_star = (not bull[0]) and bodies[1] < bodies[0] * 0.3 and bull[2] and \
                bodies[0] > 0 and bodies[2] > 0 and c[2] > (o[0] + c[0]) / 2
    # Evening Star
    eve_star = bull[0] and bodies[1] < bodies[0] * 0.3 and (not bull[2]) and \
               bodies[0] > 0 and bodies[2] > 0 and c[2] < (o[0] + c[0]) / 2
    # Three Inside Up: bear engulfed by bull harami, then close > prior open
    tiu = (not bull[0]) and bull[1] and o[1] > c[0] and c[1] < o[0] and \
          bull[2] and c[2] > o[0]
    # Three Inside Down
    tid = bull[0] and (not bull[1]) and o[1] < c[0] and c[1] > o[0] and \
          (not bull[2]) and c[2] < o[0]
    payload = {"three_white_soldiers": three_white, "three_black_crows": three_black,
               "morning_star": morn_star, "evening_star": eve_star,
               "three_inside_up": tiu, "three_inside_down": tid}
    if three_white or morn_star or tiu:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if three_black or eve_star or tid:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class JapaneseCandlesticksAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
