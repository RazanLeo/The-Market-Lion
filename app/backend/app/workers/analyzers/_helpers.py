"""Shared helpers used across all analyzer packs."""
from __future__ import annotations
import numpy as np
import pandas as pd


def swings(df: pd.DataFrame, n: int = 5):
    """Indices of swing highs and lows using fractal of size n."""
    highs, lows = [], []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max(): highs.append(i)
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min(): lows.append(i)
    return highs, lows


def atr(df: pd.DataFrame, period: int = 14) -> float:
    if len(df) < period + 1: return float(df["c"].iloc[-1] * 0.005) if len(df) else 1.0
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def sma(s: pd.Series, span: int) -> pd.Series:
    return s.rolling(span).mean()


def rsi_series(c: pd.Series, period: int = 14) -> pd.Series:
    d = c.diff()
    g = d.where(d > 0, 0).ewm(alpha=1/period, adjust=False).mean()
    l = -d.where(d < 0, 0).ewm(alpha=1/period, adjust=False).mean()
    rs = g / l.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def safe_score(value: float, lo: float, hi: float) -> float:
    """Clamp normalized score to [0,100]."""
    if value <= lo: return 0.0
    if value >= hi: return 100.0
    return (value - lo) / (hi - lo) * 100


def latest_bar(df: pd.DataFrame):
    return df.iloc[-1] if len(df) else None


def slope(s: pd.Series, window: int = 10) -> float:
    if len(s) < window: return 0.0
    y = s.tail(window).to_numpy()
    x = np.arange(len(y))
    return float(np.polyfit(x, y, 1)[0])


def stddev_channel(c: pd.Series, period: int = 50, mult: float = 2.0):
    m = c.rolling(period).mean()
    sd = c.rolling(period).std()
    return m - mult * sd, m, m + mult * sd


def linreg_channel(c: pd.Series, period: int = 100):
    if len(c) < period: return None, None, None
    y = c.tail(period).to_numpy()
    x = np.arange(period)
    a, b = np.polyfit(x, y, 1)
    fit = a * x + b
    res = y - fit
    sd = res.std()
    return fit[-1] - 2*sd, fit[-1], fit[-1] + 2*sd


def true_range(df: pd.DataFrame) -> pd.Series:
    h, l, c = df["h"], df["l"], df["c"]
    return pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
