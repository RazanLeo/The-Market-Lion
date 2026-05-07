"""Stooq.com — free CSV-over-HTTPS data source. No API key, no rate limit notices.

Used as a fallback when yfinance is blocked by the network. Returns the same
DataFrame shape: index=UTC, columns=[o, h, l, c, v].
"""
from __future__ import annotations

import io
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd

from ...core.logging import get_logger

log = get_logger("stooq")

# Symbol -> Stooq ticker code
SYMBOL_TO_STOOQ: dict[str, str] = {
    # Metals & energy
    "XAUUSD": "xauusd",  "XAGUSD": "xagusd",
    "USOIL":  "cl.f",    "BRENT":  "bz.f",
    "NATGAS": "ng.f",
    # FX
    "EURUSD": "eurusd",  "GBPUSD": "gbpusd",  "USDJPY": "usdjpy",
    "USDCHF": "usdchf",  "USDCAD": "usdcad",  "AUDUSD": "audusd",
    "NZDUSD": "nzdusd",  "EURJPY": "eurjpy",  "GBPJPY": "gbpjpy",
    # Indices
    "DXY":    "^dxy",    "SPX":    "^spx",    "NDX":    "^ndx",
    "DJI":    "^dji",    "DAX":    "^dax",    "FTSE":   "^ftm",
    # Crypto
    "BTCUSD": "btcusd",  "ETHUSD": "ethusd",
}

# Stooq supports d (daily), w (weekly). For intraday we use the i 5m endpoint via /q endpoint.
TF_TO_STOOQ_INTERVAL = {
    "1D": "d", "1W": "w", "1H": "d", "4H": "d",  # falls through to daily for higher timeframes
    "1M": "5", "5M": "5", "15M": "5", "30M": "5",  # all intraday → 5-min
}

_CACHE: dict[tuple, tuple[float, pd.DataFrame]] = {}
_TTL = 30


def stooq_ohlcv(symbol: str, tf: str = "15M", bars: int = 300) -> pd.DataFrame:
    """Fetch OHLCV from Stooq. Returns empty df on any failure."""
    ticker = SYMBOL_TO_STOOQ.get(symbol.upper())
    if not ticker:
        return pd.DataFrame()

    interval = TF_TO_STOOQ_INTERVAL.get(tf.upper(), "d")
    cache_key = (ticker, interval)
    now = time.time()
    if cache_key in _CACHE:
        ts, df = _CACHE[cache_key]
        if now - ts < _TTL:
            return df.tail(bars).copy()

    try:
        # Stooq daily CSV: https://stooq.com/q/d/l/?s=eurusd&i=d
        url = f"https://stooq.com/q/d/l/?s={ticker}&i={interval}"
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code != 200 or not resp.text or "no data" in resp.text.lower():
                return pd.DataFrame()
            csv_text = resp.text
    except Exception as e:  # pragma: no cover
        log.warning("stooq_fetch_failed", symbol=symbol, err=str(e))
        return pd.DataFrame()

    try:
        df_raw = pd.read_csv(io.StringIO(csv_text))
        df_raw.columns = [c.strip().lower() for c in df_raw.columns]
        if "date" not in df_raw.columns:
            return pd.DataFrame()
        idx = pd.to_datetime(df_raw["date"] + (" " + df_raw["time"] if "time" in df_raw.columns else ""), utc=True, errors="coerce")
        df = pd.DataFrame({
            "o": df_raw["open"].astype(float),
            "h": df_raw["high"].astype(float),
            "l": df_raw["low"].astype(float),
            "c": df_raw["close"].astype(float),
            "v": df_raw.get("volume", pd.Series(0.0, index=df_raw.index)).astype(float),
        }, index=idx)
        df = df.dropna()
        # Resample for higher TFs we don't have native intraday for
        if tf.upper() == "1H" and interval == "5":
            df = df.resample("1h").agg({"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum"}).dropna()
        elif tf.upper() == "4H":
            df = df.resample("4h").agg({"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum"}).dropna()
        _CACHE[cache_key] = (now, df)
        return df.tail(bars).copy()
    except Exception as e:  # pragma: no cover
        log.warning("stooq_parse_failed", symbol=symbol, err=str(e))
        return pd.DataFrame()


def stooq_quote(symbol: str) -> dict[str, Any]:
    """Fetch a single live quote from Stooq's q endpoint."""
    ticker = SYMBOL_TO_STOOQ.get(symbol.upper())
    if not ticker:
        return {}
    try:
        url = f"https://stooq.com/q/l/?s={ticker}&f=sd2t2ohlcv&h&e=csv"
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return {}
            df = pd.read_csv(io.StringIO(resp.text))
            df.columns = [c.strip().lower() for c in df.columns]
            row = df.iloc[0]
            close = float(row["close"])
            open_ = float(row["open"])
            change_pct = ((close - open_) / open_ * 100) if open_ else 0
            return {
                "symbol": symbol.upper(),
                "price": round(close, 4 if close < 10 else 2),
                "changePct": round(change_pct, 2),
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "stooq",
            }
    except Exception as e:  # pragma: no cover
        log.warning("stooq_quote_failed", symbol=symbol, err=str(e))
        return {}
