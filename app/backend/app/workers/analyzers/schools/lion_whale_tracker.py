"""Lion Whale Tracker — bars with volume > 3× rolling 50-bar average.

For last 20 bars: count whale events on up-bars vs down-bars.
Dominant side = the side with more whale events in the last 20 bars.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_whale_tracker"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 70 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    avg_v = df["v"].rolling(50).mean()
    is_whale = df["v"] > avg_v * 3
    win = df.iloc[-20:]; whale_win = is_whale.iloc[-20:]
    up_bars = win["c"] > win["o"]
    whale_up = int((whale_win & up_bars).sum())
    whale_down = int((whale_win & ~up_bars).sum())
    last_whale_idx = None
    last_whale_side = None
    for i in range(len(df) - 1, max(len(df) - 30, 0), -1):
        if bool(is_whale.iloc[i]):
            last_whale_idx = i
            last_whale_side = "buy" if df["c"].iloc[i] > df["o"].iloc[i] else "sell"
            break
    bars_since_last_whale = (len(df) - 1 - last_whale_idx) if last_whale_idx is not None else None
    payload = {"whale_up_20bars": whale_up, "whale_down_20bars": whale_down,
               "last_whale_side": last_whale_side, "bars_since_last_whale": bars_since_last_whale}
    if whale_up >= 2 and whale_up > whale_down + 1:
        return AnalyzerResult(CODE, "buy", min(80.0, 45 + whale_up * 8), WEIGHT_DEFAULT, payload)
    if whale_down >= 2 and whale_down > whale_up + 1:
        return AnalyzerResult(CODE, "sell", min(80.0, 45 + whale_down * 8), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionWhaleTrackerAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
