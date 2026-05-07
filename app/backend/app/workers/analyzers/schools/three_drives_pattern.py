"""Three Drives Pattern — sequential drives at 1.272 / 1.618 fibonacci extensions.

For a Three-Drives-To-Top (sell):
  drive1 = leg from L0 to H1
  retrace1 = H1 to L1 (0.618 of drive1)
  drive2 = L1 to H2 ; expects H2 ≈ H1 + 1.272×drive1 → from L0
  retrace2 = H2 to L2
  drive3 = L2 to H3 ; expects H3 ≈ H2 + 1.272×drive2 → from L1
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "three_drives_pattern"
WEIGHT_DEFAULT = 1.0


def _swings(df: pd.DataFrame, n: int = 4):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    pivs = _swings(df, 4)
    if len(pivs) < 7:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last7 = pivs[-7:]
    types = "".join(p[1] for p in last7)

    bearish = types == "LHLHLHL" or types == "HLHLHLH"  # require alternation
    bullish = False
    sell_setup = False
    buy_setup = False
    if types == "LHLHLHL":
        # drives are at indices 1, 3, 5 (Hs)
        L0, H1, L1, H2, L2, H3, L3 = (p[2] for p in last7)
        d1 = H1 - L0; d2 = H2 - L1; d3 = H3 - L2
        ext1 = (H2 - L0) / d1 if d1 > 0 else 0
        ext2 = (H3 - L1) / d2 if d2 > 0 else 0
        if 1.20 <= ext1 <= 1.70 and 1.20 <= ext2 <= 1.70 and H3 > H2 > H1:
            sell_setup = True
            payload_pts = {"drive1_high": H1, "drive2_high": H2, "drive3_high": H3,
                           "ext1": round(ext1, 3), "ext2": round(ext2, 3)}
    if types == "HLHLHLH":
        H0, L1, H1b, L2, H2b, L3, H3b = (p[2] for p in last7)
        d1 = H0 - L1; d2 = H1b - L2; d3 = H2b - L3
        ext1 = (H0 - L2) / d1 if d1 > 0 else 0
        ext2 = (H1b - L3) / d2 if d2 > 0 else 0
        if 1.20 <= ext1 <= 1.70 and 1.20 <= ext2 <= 1.70 and L3 < L2 < L1:
            buy_setup = True
            payload_pts = {"drive1_low": L1, "drive2_low": L2, "drive3_low": L3,
                           "ext1": round(ext1, 3), "ext2": round(ext2, 3)}

    if not (sell_setup or buy_setup):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types})

    last_close = float(df["c"].iloc[-1])
    if sell_setup:
        return AnalyzerResult(CODE, "sell", 75.0, WEIGHT_DEFAULT, {**payload_pts, "completion": True})
    return AnalyzerResult(CODE, "buy", 75.0, WEIGHT_DEFAULT, {**payload_pts, "completion": True})


class ThreeDrivesPatternAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
