"""Production analyzers — first 7 indicators (RSI, EMA Stack, MACD, VWAP, Bollinger, ATR, ADX).

Each function takes an OHLCV pandas DataFrame indexed by timestamp with columns
[o, h, l, c, v] and returns an AnalyzerResult-shaped dict.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..engines.voting_engine import AnalyzerResult


# ── RSI ─────────────────────────────────────────────────────────────
def _rsi(c: pd.Series, period: int = 14) -> pd.Series:
    d = c.diff()
    g = d.where(d > 0, 0).ewm(alpha=1/period, adjust=False).mean()
    l = -d.where(d < 0, 0).ewm(alpha=1/period, adjust=False).mean()
    rs = g / l.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def rsi_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult("rsi", "neutral", 0.0, 1.0, {})
    rsi = _rsi(df["c"]).iloc[-1]
    rsi_prev = _rsi(df["c"]).iloc[-5] if len(df) > 50 else rsi
    # divergence
    price_hh = df["c"].iloc[-1] > df["c"].iloc[-5]
    rsi_hh = rsi > rsi_prev
    bullish_div = (df["c"].iloc[-1] < df["c"].iloc[-10]) and (rsi > _rsi(df["c"]).iloc[-10])
    bearish_div = price_hh and (not rsi_hh)
    if rsi < 30 or bullish_div:
        return AnalyzerResult("rsi", "buy", min(80, 50 + (30 - rsi) * 2 if rsi < 30 else 70), 1.0, {"rsi": float(rsi), "div": "bullish" if bullish_div else None})
    if rsi > 70 or bearish_div:
        return AnalyzerResult("rsi", "sell", min(80, 50 + (rsi - 70) * 2 if rsi > 70 else 70), 1.0, {"rsi": float(rsi), "div": "bearish" if bearish_div else None})
    if rsi > 55:
        return AnalyzerResult("rsi", "buy", 30 + (rsi - 55) * 2, 1.0, {"rsi": float(rsi)})
    if rsi < 45:
        return AnalyzerResult("rsi", "sell", 30 + (45 - rsi) * 2, 1.0, {"rsi": float(rsi)})
    return AnalyzerResult("rsi", "neutral", 0.0, 1.0, {"rsi": float(rsi)})


# ── EMA Stack (7/21/60/200 + FRAMA126) ──────────────────────────────
def ema_stack_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200:
        return AnalyzerResult("ema_stack", "neutral", 0.0, 1.0, {})
    c = df["c"]
    e7 = c.ewm(span=7, adjust=False).mean().iloc[-1]
    e21 = c.ewm(span=21, adjust=False).mean().iloc[-1]
    s60 = c.rolling(60).mean().iloc[-1]
    s200 = c.rolling(200).mean().iloc[-1]
    last = c.iloc[-1]
    bull_stack = last > e7 > e21 > s60 > s200
    bear_stack = last < e7 < e21 < s60 < s200
    if bull_stack:
        score = 70 + min(20, (last - s200) / s200 * 1000)
        return AnalyzerResult("ema_stack", "buy", min(95, score), 1.0, {"e7": e7, "e21": e21, "s60": s60, "s200": s200})
    if bear_stack:
        score = 70 + min(20, (s200 - last) / s200 * 1000)
        return AnalyzerResult("ema_stack", "sell", min(95, score), 1.0, {"e7": e7, "e21": e21, "s60": s60, "s200": s200})
    if last > s200 and e7 > e21:
        return AnalyzerResult("ema_stack", "buy", 50, 1.0, {})
    if last < s200 and e7 < e21:
        return AnalyzerResult("ema_stack", "sell", 50, 1.0, {})
    return AnalyzerResult("ema_stack", "neutral", 0, 1.0, {})


# ── MACD ────────────────────────────────────────────────────────────
def macd_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult("macd", "neutral", 0, 1.0, {})
    c = df["c"]
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    cross_up = macd.iloc[-2] <= signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]
    cross_dn = macd.iloc[-2] >= signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1]
    h = float(hist.iloc[-1])
    if cross_up:
        return AnalyzerResult("macd", "buy", 75, 1.0, {"macd": float(macd.iloc[-1]), "hist": h})
    if cross_dn:
        return AnalyzerResult("macd", "sell", 75, 1.0, {"macd": float(macd.iloc[-1]), "hist": h})
    if h > 0 and macd.iloc[-1] > 0:
        return AnalyzerResult("macd", "buy", 40 + min(40, abs(h) * 100), 1.0, {})
    if h < 0 and macd.iloc[-1] < 0:
        return AnalyzerResult("macd", "sell", 40 + min(40, abs(h) * 100), 1.0, {})
    return AnalyzerResult("macd", "neutral", 0, 1.0, {})


# ── VWAP ────────────────────────────────────────────────────────────
def vwap_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20 or "v" not in df.columns:
        return AnalyzerResult("vwap", "neutral", 0, 1.0, {})
    v = df["v"].fillna(1.0).replace(0, 1.0)
    tp = (df["h"] + df["l"] + df["c"]) / 3
    vwap = (tp * v).cumsum() / v.cumsum()
    last = float(df["c"].iloc[-1])
    vw = float(vwap.iloc[-1])
    diff = (last - vw) / vw * 100
    if diff > 0.05:
        return AnalyzerResult("vwap", "buy", min(80, 40 + diff * 200), 1.0, {"vwap": vw})
    if diff < -0.05:
        return AnalyzerResult("vwap", "sell", min(80, 40 + abs(diff) * 200), 1.0, {"vwap": vw})
    return AnalyzerResult("vwap", "neutral", 0, 1.0, {"vwap": vw})


# ── Bollinger Bands ─────────────────────────────────────────────────
def bollinger_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("bollinger", "neutral", 0, 1.0, {})
    c = df["c"]
    ma = c.rolling(20).mean()
    sd = c.rolling(20).std()
    upper = ma + 2 * sd
    lower = ma - 2 * sd
    pctb = (c.iloc[-1] - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1] + 1e-9)
    bw = (upper.iloc[-1] - lower.iloc[-1]) / ma.iloc[-1]
    bw_avg = ((upper - lower) / ma).rolling(50).mean().iloc[-1]
    squeeze = bw < bw_avg * 0.8
    if squeeze:
        # squeeze break direction
        if c.iloc[-1] > upper.iloc[-2]:
            return AnalyzerResult("bollinger", "buy", 80, 1.0, {"squeeze_break": "up", "%b": float(pctb)})
        if c.iloc[-1] < lower.iloc[-2]:
            return AnalyzerResult("bollinger", "sell", 80, 1.0, {"squeeze_break": "down", "%b": float(pctb)})
    if pctb > 1:
        return AnalyzerResult("bollinger", "sell", 60, 1.0, {"reason": "above_upper"})
    if pctb < 0:
        return AnalyzerResult("bollinger", "buy", 60, 1.0, {"reason": "below_lower"})
    return AnalyzerResult("bollinger", "neutral", 0, 1.0, {"%b": float(pctb)})


# ── ATR / Volatility gate ──────────────────────────────────────────
def atr_volatility_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("atr_vol", "neutral", 0, 1.0, {})
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    atr_ratio = atr.iloc[-1] / atr.rolling(50).mean().iloc[-1]
    # Pure volatility doesn't directly buy/sell — return neutral but expose info.
    return AnalyzerResult("atr_vol", "neutral", 0, 0.5, {"atr": float(atr.iloc[-1]), "atr_ratio": float(atr_ratio)})


# ── ADX / DMI ───────────────────────────────────────────────────────
def adx_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("adx", "neutral", 0, 1.0, {})
    h, l, c = df["h"], df["l"], df["c"]
    up = h.diff()
    dn = -l.diff()
    plus_dm = up.where((up > dn) & (up > 0), 0)
    minus_dm = dn.where((dn > up) & (dn > 0), 0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1)
    adx = dx.ewm(alpha=1/14, adjust=False).mean().iloc[-1]
    pdi, mdi = float(plus_di.iloc[-1]), float(minus_di.iloc[-1])
    if adx > 25 and pdi > mdi:
        return AnalyzerResult("adx", "buy", min(85, 50 + (adx - 25) * 1.5), 1.0, {"adx": float(adx), "+DI": pdi, "-DI": mdi})
    if adx > 25 and mdi > pdi:
        return AnalyzerResult("adx", "sell", min(85, 50 + (adx - 25) * 1.5), 1.0, {"adx": float(adx), "+DI": pdi, "-DI": mdi})
    return AnalyzerResult("adx", "neutral", 0, 1.0, {"adx": float(adx)})
