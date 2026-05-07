"""Free open data sources for The Market Lion analysis engine.

The platform analyzes prices using publicly-available, free data feeds:
  1. Yahoo Finance (yfinance) — primary OHLCV for forex, commodities, stocks, crypto
  2. Stooq — fallback CSV-over-HTTPS source
  3. TradingView public symbol mapping — for chart embedding (no API key required)

Capital.com / Exness are NOT used for analysis — they are only used as
execution brokers when a user links their personal account to enable the
auto-trading bot. All analytics are computed from the free feeds above.
"""
from __future__ import annotations
import pandas as pd
from typing import Any
from .yahoo import yahoo_ohlcv, yahoo_quote, SYMBOL_TO_YAHOO
from .stooq import stooq_ohlcv, stooq_quote, SYMBOL_TO_STOOQ
from ...core.logging import get_logger

log = get_logger("data_sources")


def get_ohlcv(symbol: str, tf: str = "15M", bars: int = 300) -> pd.DataFrame:
    """Try Yahoo first, fall back to Stooq. Returns empty df only if BOTH fail."""
    df = yahoo_ohlcv(symbol, tf, bars)
    if not df.empty and len(df) >= 30:
        return df
    log.info("falling_back_to_stooq", symbol=symbol, tf=tf)
    df = stooq_ohlcv(symbol, tf, bars)
    return df


def get_quote(symbol: str) -> dict[str, Any]:
    """Try Yahoo first, fall back to Stooq."""
    q = yahoo_quote(symbol)
    if q and q.get("price"):
        return q
    return stooq_quote(symbol)


__all__ = [
    "get_ohlcv", "get_quote",
    "yahoo_ohlcv", "yahoo_quote", "SYMBOL_TO_YAHOO",
    "stooq_ohlcv", "stooq_quote", "SYMBOL_TO_STOOQ",
]
