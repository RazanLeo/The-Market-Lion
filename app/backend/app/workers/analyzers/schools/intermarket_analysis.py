"""Intermarket Analysis (John Murphy) — relationship between markets via price-return correlations.

Without external feeds, we approximate with self-shifted comparisons:
  • lead_return = pct_change of lagged close (5 bars ahead vs current)
  • follow_return = pct_change of current close
Correlation between lead and follow = leading-indicator strength.
Divergence = price up but rolling 50-bar correlation flips negative → regime change.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "intermarket_analysis"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 100:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ret = df["c"].pct_change()
    lead = ret.shift(-5)
    win = pd.concat([ret, lead], axis=1).dropna().iloc[-50:]
    if len(win) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    corr = float(win.iloc[:, 0].corr(win.iloc[:, 1]) or 0)
    # 50-bar rolling correlation of close & 14-period SMA (proxy for "trend leadership")
    sma14 = df["c"].rolling(14).mean()
    rcorr = float(df["c"].iloc[-50:].corr(sma14.iloc[-50:]) or 0)
    direction_now = float(df["c"].iloc[-1]) > float(df["c"].iloc[-20])
    diverging = direction_now and rcorr < 0
    payload = {"lead_follow_corr": round(corr, 3), "trend_leadership_corr": round(rcorr, 3),
               "diverging": diverging}
    if rcorr > 0.5 and direction_now:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if rcorr > 0.5 and not direction_now:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    if diverging:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class IntermarketAnalysisAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
