"""Lion Whale Indicator — volume bar > 3× rolling 50-bar average.

Detects "whale" prints (institutional-size volume bars). Counts events in last 20 bars.
Direction inferred from bar's price action: green whale = accumulation, red whale =
distribution.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_whale_indicator"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    vol_avg = df["v"].rolling(50).mean()
    is_whale = df["v"] > 3 * vol_avg
    last20 = is_whale.iloc[-20:]
    whales_total = int(last20.sum())
    bars_up = (df["c"] > df["o"])
    bars_dn = (df["c"] < df["o"])
    bull_whales = int((last20 & bars_up.iloc[-20:]).sum())
    bear_whales = int((last20 & bars_dn.iloc[-20:]).sum())
    last_is_whale = bool(is_whale.iloc[-1])
    last_dir_up = float(df["c"].iloc[-1]) > float(df["o"].iloc[-1])
    payload = {"whale_events_20b": whales_total,
               "bull_whales_20b": bull_whales, "bear_whales_20b": bear_whales,
               "last_bar_whale": last_is_whale,
               "last_whale_side": "buy" if last_is_whale and last_dir_up else
                                  "sell" if last_is_whale and not last_dir_up else "none"}
    if last_is_whale and last_dir_up:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if last_is_whale and not last_dir_up:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if bull_whales >= 3 and bull_whales > bear_whales * 2:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if bear_whales >= 3 and bear_whales > bull_whales * 2:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionWhaleIndicatorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
