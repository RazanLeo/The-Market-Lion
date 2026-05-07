"""Killzones London/NY — directional bias during ICT killzones.

London KZ: 07-10 UTC. NY KZ: 12-15 UTC. Within these windows, a strong directional bar
(range ≥ 1.5×ATR) is the highest-probability "killzone" trade. Outside these hours = no
signal (returns neutral).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "killzones_london_ny"
WEIGHT_DEFAULT = 0.95


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    hr = df.index[-1].hour
    in_london = 7 <= hr <= 10
    in_ny = 12 <= hr <= 15
    in_kz = in_london or in_ny
    if not in_kz:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT,
                              {"in_killzone": False, "hour_utc": hr})
    atr = _atr(df)
    bar_range = float(df["h"].iloc[-1] - df["l"].iloc[-1])
    big_bar = bar_range >= 1.5 * atr if atr > 0 else False
    direction = float(df["c"].iloc[-1]) - float(df["o"].iloc[-1])
    payload = {"in_killzone": True, "kz": "London" if in_london else "NY",
               "hour_utc": hr, "big_bar": big_bar,
               "range_atr": round(bar_range / atr, 2) if atr > 0 else 0}
    if big_bar and direction > 0:
        return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if big_bar and direction < 0:
        return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)


class KillzonesLondonNyAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
