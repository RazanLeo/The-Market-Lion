"""Market data endpoints — public ticker prices for the homepage strip & widgets.

Data source = Yahoo Finance (free, public, no API key). Cached in Redis for 5s.
Capital.com is NEVER used for analysis data — only for execution when the user
links a broker account in their settings.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import redis as redis_sync
from fastapi import APIRouter, Depends

from ..core.config import settings
from ..core.logging import get_logger
from ..deps import current_user_optional
from ..services.data_sources import get_quote as yahoo_quote, get_ohlcv

router = APIRouter()
log = get_logger("market")

WATCHLIST = ["XAUUSD", "USOIL", "BRENT", "EURUSD", "GBPUSD", "USDJPY",
             "USDCHF", "USDCAD", "AUDUSD", "NZDUSD", "XAGUSD", "DXY"]

CACHE_KEY = "market:tickers:v2"
CACHE_TTL_SEC = 10  # 10s — Yahoo is free but courteous


def _live_snapshot() -> list[dict]:
    """Pull fresh quotes from Yahoo Finance for the entire watchlist."""
    out = []
    for sym in WATCHLIST:
        q = yahoo_quote(sym)
        if q:
            out.append(q)
    return out


@router.get("/tickers")
async def tickers(user=Depends(current_user_optional)):
    """Public endpoint — returns live price + 24h pct change for each symbol."""
    try:
        r = redis_sync.from_url(settings.REDIS_URL, decode_responses=True)
        cached = r.get(CACHE_KEY)
        if cached:
            return {"ok": True, "tickers": json.loads(cached), "cached": True}
    except Exception:  # pragma: no cover
        r = None

    snapshot = _live_snapshot()

    if r is not None and snapshot:
        try:
            r.setex(CACHE_KEY, CACHE_TTL_SEC, json.dumps(snapshot))
        except Exception:  # pragma: no cover
            pass

    return {"ok": True, "tickers": snapshot, "cached": False,
            "source": "yahoo", "ts": datetime.now(timezone.utc).isoformat()}


@router.get("/ohlcv")
async def ohlcv(symbol: str, tf: str = "15M", bars: int = 200,
                user=Depends(current_user_optional)):
    """Return raw OHLCV history for the chart component."""
    df = get_ohlcv(symbol, tf, bars)
    if df.empty:
        return {"ok": False, "error": "no_data", "symbol": symbol, "tf": tf}
    return {
        "ok": True, "symbol": symbol, "tf": tf, "source": "yahoo",
        "candles": [
            {"time": int(t.timestamp()), "open": float(r["o"]), "high": float(r["h"]),
             "low": float(r["l"]), "close": float(r["c"]), "volume": float(r["v"])}
            for t, r in df.iterrows()
        ],
    }
