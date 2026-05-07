"""Multi-Timeframe (MTF) Structure Alignment — emulating 1H / 4H / 1D HH/HL/LH/LL classification on
a single OHLCV series by resampling.

If the dataframe is at 15m granularity, we resample to 1H/4H/1D and check structure on each:
  • bullish_struct(tf): the last two swing-high pivots are higher AND the last two swing-low pivots are higher.
  • bearish_struct(tf): mirror.
Alignment = same direction across all 3 TFs.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "moltbook_school"
WEIGHT_DEFAULT = 1.05


def _swings(df: pd.DataFrame, n: int = 3):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def _structure(df: pd.DataFrame) -> str:
    if len(df) < 30: return "unknown"
    pivs = _swings(df, 3)
    highs = [p for p in pivs if p[1] == "H"][-2:]
    lows = [p for p in pivs if p[1] == "L"][-2:]
    if len(highs) < 2 or len(lows) < 2: return "unknown"
    if highs[1][2] > highs[0][2] and lows[1][2] > lows[0][2]: return "bullish"
    if highs[1][2] < highs[0][2] and lows[1][2] < lows[0][2]: return "bearish"
    return "mixed"


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    def _resample(rule: str) -> pd.DataFrame:
        return df.resample(rule).agg({"o": "first", "h": "max", "l": "min", "c": "last",
                                       "v": "sum" if "v" in df.columns else "size"}).dropna()

    h1 = _resample("1h")
    h4 = _resample("4h")
    d1 = _resample("1D")

    s_h1 = _structure(h1)
    s_h4 = _structure(h4)
    s_d1 = _structure(d1)
    bull_count = sum(1 for s in (s_h1, s_h4, s_d1) if s == "bullish")
    bear_count = sum(1 for s in (s_h1, s_h4, s_d1) if s == "bearish")

    payload = {"struct_1H": s_h1, "struct_4H": s_h4, "struct_1D": s_d1,
               "bull_count": bull_count, "bear_count": bear_count}
    if bull_count >= 2 and bear_count == 0:
        return AnalyzerResult(CODE, "buy", min(85.0, 45 + bull_count * 12), WEIGHT_DEFAULT, payload)
    if bear_count >= 2 and bull_count == 0:
        return AnalyzerResult(CODE, "sell", min(85.0, 45 + bear_count * 12), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MoltbookSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
