"""Market Structure Shift (MSS) — first opposing structural break after a sustained trend.

Detect: in a downtrend (LL+LH) the *first* higher-high that exceeds the prior swing high = MSS Up.
Mirror in uptrend = MSS Down.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "market_structure_shift"
WEIGHT_DEFAULT = 1.0


def _swings(df: pd.DataFrame, n: int = 3):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 3)
    if len(pivs) < 6:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_close = float(df["c"].iloc[-1])
    # Determine prior trend from pivs[-6:-2]
    prior_highs = [p for p in pivs[-6:-2] if p[1] == "H"]
    prior_lows = [p for p in pivs[-6:-2] if p[1] == "L"]
    if len(prior_highs) < 2 or len(prior_lows) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    downtrend = prior_highs[1][2] < prior_highs[0][2] and prior_lows[1][2] < prior_lows[0][2]
    uptrend = prior_highs[1][2] > prior_highs[0][2] and prior_lows[1][2] > prior_lows[0][2]
    if not (downtrend or uptrend):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_high = max(p for p in pivs[-2:] if p[1] == "H")[2] if any(p[1] == "H" for p in pivs[-2:]) else None
    last_low = min(p for p in pivs[-2:] if p[1] == "L")[2] if any(p[1] == "L" for p in pivs[-2:]) else None
    mss_up = downtrend and last_close > prior_highs[1][2]
    mss_down = uptrend and last_close < prior_lows[1][2]
    payload = {"prior_trend": "down" if downtrend else "up",
               "broken_level": prior_highs[1][2] if mss_up else prior_lows[1][2] if mss_down else None,
               "MSS_up": mss_up, "MSS_down": mss_down}
    if mss_up: return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if mss_down: return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MarketStructureShiftAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
