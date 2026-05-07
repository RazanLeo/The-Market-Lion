"""Lion Confluence Meter — composite of 5 boolean conditions.

Counts how many of these are TRUE on the latest bar:
  • RSI(14) < 30 (bull) or > 70 (bear)
  • MACD bull/bear cross today
  • BB %B < 0 (bull) or > 1 (bear)
  • EMA(20) rising (bull) or falling (bear)
  • Volume > 1.5× 50-bar avg (any side)
≥3 of 5 = high-confluence trade signal.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_confluence_meter"
WEIGHT_DEFAULT = 1.05


def _rsi(c: pd.Series, p: int = 14) -> pd.Series:
    delta = c.diff()
    up = delta.where(delta > 0, 0).ewm(alpha=1/p, adjust=False).mean()
    dn = -delta.where(delta < 0, 0).ewm(alpha=1/p, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    rsi = _rsi(c, 14); rsi_v = float(rsi.iloc[-1])
    ema12 = c.ewm(span=12, adjust=False).mean(); ema26 = c.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26; sig = macd.ewm(span=9, adjust=False).mean()
    macd_bull_cross = float(macd.iloc[-2]) <= float(sig.iloc[-2]) and float(macd.iloc[-1]) > float(sig.iloc[-1])
    macd_bear_cross = float(macd.iloc[-2]) >= float(sig.iloc[-2]) and float(macd.iloc[-1]) < float(sig.iloc[-1])
    sma20 = c.rolling(20).mean(); sd20 = c.rolling(20).std()
    pctb = float((c.iloc[-1] - (sma20.iloc[-1] - 2 * sd20.iloc[-1])) / (4 * sd20.iloc[-1] + 1e-9))
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema_rising = float(ema20.iloc[-1]) > float(ema20.iloc[-5])
    ema_falling = float(ema20.iloc[-1]) < float(ema20.iloc[-5])
    if "v" in df.columns:
        avg_v = float(df["v"].rolling(50).mean().iloc[-1] or 1)
        last_v = float(df["v"].iloc[-1])
        vol_surge = last_v > avg_v * 1.5
    else:
        vol_surge = False
    bull_count = sum([rsi_v < 30, macd_bull_cross, pctb < 0, ema_rising, vol_surge])
    bear_count = sum([rsi_v > 70, macd_bear_cross, pctb > 1, ema_falling, vol_surge])
    payload = {"rsi": round(rsi_v, 1), "macd_bull_cross": macd_bull_cross,
               "macd_bear_cross": macd_bear_cross, "%B": round(pctb, 3),
               "ema20_rising": ema_rising, "ema20_falling": ema_falling,
               "vol_surge": vol_surge,
               "bull_count": bull_count, "bear_count": bear_count}
    if bull_count >= 3: return AnalyzerResult(CODE, "buy", min(90.0, 50 + bull_count * 10), WEIGHT_DEFAULT, payload)
    if bear_count >= 3: return AnalyzerResult(CODE, "sell", min(90.0, 50 + bear_count * 10), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionConfluenceMeterAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
