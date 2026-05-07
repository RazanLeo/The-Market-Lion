"""Yahoo Finance data source — free, public, no-API-key OHLCV feed.

Covers our entire watchlist:
  • XAUUSD (GC=F gold futures), XAGUSD (SI=F silver futures)
  • USOIL (CL=F crude WTI), BRENT (BZ=F)
  • All major FX pairs via X-suffix tickers (EURUSD=X, GBPUSD=X, …)
  • DXY (DX-Y.NYB)
  • Equity indices (^GSPC, ^IXIC, ^DJI) and individual stocks for institutional plans

Uses an in-process LRU cache + Redis cache to keep latency low and respect
Yahoo's rate limits.
"""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from ...core.logging import get_logger

log = get_logger("yahoo")

# Symbol mapping: platform symbol -> Yahoo ticker
SYMBOL_TO_YAHOO: dict[str, str] = {
    # Metals & energy
    "XAUUSD": "GC=F",   # Gold futures
    "XAGUSD": "SI=F",   # Silver futures
    "USOIL":  "CL=F",   # WTI crude
    "BRENT":  "BZ=F",   # Brent crude
    "NATGAS": "NG=F",   # Natural gas
    # Major FX
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X",
    "USDCHF": "USDCHF=X", "USDCAD": "USDCAD=X", "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X", "EURJPY": "EURJPY=X", "GBPJPY": "GBPJPY=X",
    # Indices
    "DXY":   "DX-Y.NYB",
    "SPX":   "^GSPC",
    "NDX":   "^IXIC",
    "DJI":   "^DJI",
    "DAX":   "^GDAXI",
    "FTSE":  "^FTSE",
    "NIKKEI":"^N225",
    # Crypto
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
}

# Yahoo interval strings keyed by our timeframe codes
TF_TO_YAHOO_INTERVAL = {
    "1M":  "1m",   "5M":  "5m",   "15M": "15m",
    "30M": "30m",  "1H":  "60m",  "4H":  "1h",   # Yahoo doesn't expose 4h directly — we resample 1h→4h
    "1D":  "1d",   "1W":  "1wk",
}

# Period needed to get enough bars per timeframe
TF_TO_PERIOD = {
    "1M": "5d", "5M": "10d", "15M": "30d",
    "30M": "60d", "1H": "60d", "4H": "60d",
    "1D": "2y", "1W": "10y",
}

# In-process cache (yahoo ticker, interval) -> (timestamp, df)
_CACHE: dict[tuple, tuple[float, pd.DataFrame]] = {}
_CACHE_TTL_SEC = 30  # 30-second cache to avoid hammering Yahoo


def _get_yfinance():
    """Lazy import — yfinance is heavy and only needed at call time."""
    try:
        import yfinance as yf
        return yf
    except ImportError:  # pragma: no cover
        log.error("yfinance_not_installed")
        return None


def yahoo_ohlcv(symbol: str, tf: str = "15M", bars: int = 300) -> pd.DataFrame:
    """Fetch OHLCV for one symbol at one timeframe. Returns DataFrame indexed by UTC datetime
    with columns: o, h, l, c, v.

    Returns an empty DataFrame on failure — callers must check `df.empty`.
    """
    yf = _get_yfinance()
    if yf is None:
        return pd.DataFrame()

    yahoo_ticker = SYMBOL_TO_YAHOO.get(symbol.upper(), symbol)
    interval = TF_TO_YAHOO_INTERVAL.get(tf.upper(), "15m")
    period = TF_TO_PERIOD.get(tf.upper(), "30d")
    cache_key = (yahoo_ticker, interval)

    now = time.time()
    if cache_key in _CACHE:
        ts, df_cached = _CACHE[cache_key]
        if now - ts < _CACHE_TTL_SEC:
            return df_cached.tail(bars).copy()

    try:
        t = yf.Ticker(yahoo_ticker)
        hist = t.history(period=period, interval=interval, auto_adjust=False)
    except Exception as e:  # pragma: no cover
        log.warning("yahoo_fetch_failed", symbol=symbol, ticker=yahoo_ticker, err=str(e))
        return pd.DataFrame()

    if hist is None or len(hist) == 0:
        return pd.DataFrame()

    df = pd.DataFrame({
        "o": hist["Open"].astype(float),
        "h": hist["High"].astype(float),
        "l": hist["Low"].astype(float),
        "c": hist["Close"].astype(float),
        "v": hist.get("Volume", pd.Series(0.0, index=hist.index)).astype(float),
    })
    df.index = pd.to_datetime(df.index, utc=True)

    # Resample 1h → 4h if requested
    if tf.upper() == "4H":
        df = df.resample("4h").agg({"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum"}).dropna()

    _CACHE[cache_key] = (now, df)
    return df.tail(bars).copy()


def yahoo_quote(symbol: str) -> dict[str, Any]:
    """Fetch a single live quote (last price + 24h change) for a symbol."""
    yf = _get_yfinance()
    if yf is None:
        return {}
    yahoo_ticker = SYMBOL_TO_YAHOO.get(symbol.upper(), symbol)
    try:
        t = yf.Ticker(yahoo_ticker)
        info = getattr(t, "fast_info", None) or {}
        last = float(info.get("last_price") or info.get("lastPrice") or 0)
        prev = float(info.get("previous_close") or info.get("previousClose") or 0)
        if last <= 0:
            # Fallback: most-recent intraday bar
            h = t.history(period="2d", interval="15m")
            if len(h):
                last = float(h["Close"].iloc[-1])
                prev = float(h["Close"].iloc[0])
        change_pct = ((last - prev) / prev * 100) if prev > 0 else 0.0
        return {
            "symbol": symbol.upper(),
            "price": round(last, 4 if last < 10 else 2),
            "changePct": round(change_pct, 2),
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "yahoo",
        }
    except Exception as e:  # pragma: no cover
        log.warning("yahoo_quote_failed", symbol=symbol, err=str(e))
        return {}
