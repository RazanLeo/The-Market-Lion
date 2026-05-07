"""Lion Confluence Meter — count of 5 simultaneous bullish conditions.

Counts how many of:
  1. RSI(14) < 30 (oversold) for buy / RSI > 70 for sell
  2. MACD bullish/bearish cross within last 3 bars
  3. BB %B < 0 (below lower) buy / %B > 1 sell
  4. EMA(20) rising (>= 3 bars up) buy / falling sell
  5. Volume surge (vol > 1.5× 20-bar avg)
Score 0..5. ≥4 = strong setup.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_confluence_meter_ind"
WEIGHT_DEFAULT = 1.0


def _rsi(c, n=14):
    diff = c.diff()
    up = diff.clip(lower=0); dn = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / (ad + 1e-9))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    rsi = float(_rsi(c).iloc[-1])
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    sig = macd.ewm(span=9, adjust=False).mean()
    macd_diff = (macd - sig).iloc[-3:]
    bull_macd = bool((macd_diff.iloc[-1] > 0) and any(macd_diff.iloc[i] <= 0 for i in range(2)))
    bear_macd = bool((macd_diff.iloc[-1] < 0) and any(macd_diff.iloc[i] >= 0 for i in range(2)))
    sma = c.rolling(20).mean(); sd = c.rolling(20).std()
    pct_b = float(((c - (sma - 2 * sd)) / (4 * sd + 1e-9)).iloc[-1])
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema_rising = float(ema20.iloc[-1]) > float(ema20.iloc[-3]) > float(ema20.iloc[-5])
    ema_falling = float(ema20.iloc[-1]) < float(ema20.iloc[-3]) < float(ema20.iloc[-5])
    vol_surge = float(df["v"].iloc[-1]) > 1.5 * float(df["v"].rolling(20).mean().iloc[-1] or 1)
    bull_score = sum([rsi < 30, bull_macd, pct_b < 0, ema_rising, vol_surge])
    bear_score = sum([rsi > 70, bear_macd, pct_b > 1, ema_falling, vol_surge])
    payload = {"rsi": round(rsi, 1), "pct_b": round(pct_b, 3),
               "bull_score": int(bull_score), "bear_score": int(bear_score),
               "ema_trend": "rising" if ema_rising else "falling" if ema_falling else "flat"}
    if bull_score >= 4:
        return AnalyzerResult(CODE, "buy", min(90, 50 + bull_score * 10), WEIGHT_DEFAULT, payload)
    if bear_score >= 4:
        return AnalyzerResult(CODE, "sell", min(90, 50 + bear_score * 10), WEIGHT_DEFAULT, payload)
    if bull_score >= 3:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if bear_score >= 3:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionConfluenceMeterIndAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
