"""Turtle Trading (Dennis & Eckhardt) — Donchian channel breakouts with ATR-based unit sizing.

System 1: Enter LONG when close breaks above 20-bar high; exit on close below 10-bar low.
          Enter SHORT mirror.
System 2: Same with 55-bar / 20-bar.
N (volatility unit) = 20-bar ATR. Position size = (1% account risk) / (N × point_value).
Add up to 4 units, each at +0.5N from entry.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "turtle_trading"
WEIGHT_DEFAULT = 1.0


def _atr(df: pd.DataFrame, period: int = 20) -> float:
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last = float(df["c"].iloc[-1])
    high20 = float(df["h"].iloc[-21:-1].max())
    low20 = float(df["l"].iloc[-21:-1].min())
    high55 = float(df["h"].iloc[-56:-1].max())
    low55 = float(df["l"].iloc[-56:-1].min())
    high10 = float(df["h"].iloc[-11:-1].max())
    low10 = float(df["l"].iloc[-11:-1].min())
    N = _atr(df, 20)

    s1_long = last > high20
    s1_short = last < low20
    s2_long = last > high55
    s2_short = last < low55
    exit_long = last < low10  # exit longs
    exit_short = last > high10

    payload = {"high20": round(high20, 5), "low20": round(low20, 5),
               "high55": round(high55, 5), "low55": round(low55, 5),
               "N_atr20": round(N, 5),
               "S1_long_break": s1_long, "S1_short_break": s1_short,
               "S2_long_break": s2_long, "S2_short_break": s2_short,
               "exit_long_signal": exit_long, "exit_short_signal": exit_short,
               "add_unit_at_long": round(last + 0.5 * N, 5),
               "add_unit_at_short": round(last - 0.5 * N, 5),
               "stop_long": round(last - 2 * N, 5), "stop_short": round(last + 2 * N, 5)}
    if s2_long: return AnalyzerResult(CODE, "buy", 85, WEIGHT_DEFAULT, payload)
    if s2_short: return AnalyzerResult(CODE, "sell", 85, WEIGHT_DEFAULT, payload)
    if s1_long: return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if s1_short: return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class TurtleTradingAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
