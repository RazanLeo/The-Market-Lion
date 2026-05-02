"""Market data router: prices, candles, symbols, WebSocket streaming."""
import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, Depends

from config import settings
from services.capital_com import CapitalComService, SYMBOL_MAP

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["Market Data"])

SUPPORTED_SYMBOLS = list(SYMBOL_MAP.keys())

# Fallback Yahoo Finance symbol map
YF_MAP = {
    "XAU/USD": "GC=F",
    "XAG/USD": "SI=F",
    "WTI/USD": "CL=F",
    "Brent/USD": "BZ=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "GBP/JPY": "GBPJPY=X",
    "EUR/JPY": "EURJPY=X",
    "DXY": "DX-Y.NYB",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
}

# Simple in-memory price cache: {symbol: {"price": float, "ts": float}}
_price_cache: dict = {}
_CACHE_TTL = 10  # seconds


# ── Price fetching helpers ────────────────────────────────────────────────────

async def _fetch_price_capital(symbol: str) -> Optional[float]:
    """Fetch latest price from Capital.com API."""
    if not settings.CAPITAL_COM_IDENTIFIER or not settings.CAPITAL_COM_PASSWORD:
        return None
    try:
        svc = CapitalComService(demo=settings.CAPITAL_COM_DEMO)
        await svc.create_session()
        epic = CapitalComService.symbol_to_epic(symbol)
        if not epic:
            return None
        data = await svc.get_market_prices(epic)
        await svc.close()
        # Capital.com returns snapshot.bid / snapshot.offer
        snapshot = data.get("snapshot", {})
        bid = snapshot.get("bid") or snapshot.get("price")
        offer = snapshot.get("offer")
        if bid and offer:
            return (float(bid) + float(offer)) / 2
        if bid:
            return float(bid)
        return None
    except Exception as e:
        logger.debug(f"Capital.com price fetch failed for {symbol}: {e}")
        return None


async def _fetch_price_yfinance(symbol: str) -> Optional[float]:
    """Fetch price via Yahoo Finance as fallback."""
    ticker = YF_MAP.get(symbol)
    if not ticker:
        return None
    try:
        import yfinance as yf
        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: yf.Ticker(ticker).fast_info,
        )
        price = getattr(data, "last_price", None) or getattr(data, "regularMarketPrice", None)
        return float(price) if price else None
    except Exception as e:
        logger.debug(f"YFinance price fetch failed for {symbol}: {e}")
        return None


def _mock_price(symbol: str) -> float:
    """Return a realistic mock price for demo/fallback."""
    BASE_PRICES = {
        "XAU/USD": 2345.0,
        "XAG/USD": 29.5,
        "WTI/USD": 78.5,
        "Brent/USD": 82.3,
        "EUR/USD": 1.0820,
        "GBP/USD": 1.2650,
        "USD/JPY": 151.50,
        "AUD/USD": 0.6520,
        "USD/CAD": 1.3680,
        "NZD/USD": 0.5980,
        "EUR/GBP": 0.8560,
        "GBP/JPY": 191.50,
        "EUR/JPY": 163.90,
        "DXY": 105.20,
        "BTC/USD": 67500.0,
        "ETH/USD": 3150.0,
    }
    base = BASE_PRICES.get(symbol, 100.0)
    # Add small random noise
    noise = base * random.uniform(-0.002, 0.002)
    return round(base + noise, 5)


async def get_price(symbol: str) -> float:
    """Get current price with caching."""
    import time
    cached = _price_cache.get(symbol)
    if cached and (time.time() - cached["ts"]) < _CACHE_TTL:
        return cached["price"]

    price = await _fetch_price_capital(symbol)
    if price is None:
        price = await _fetch_price_yfinance(symbol)
    if price is None:
        price = _mock_price(symbol)

    _price_cache[symbol] = {"price": price, "ts": __import__("time").time()}
    return price


async def _fetch_candles_capital(symbol: str, timeframe: str, count: int) -> Optional[list]:
    """Fetch historical candles from Capital.com."""
    if not settings.CAPITAL_COM_IDENTIFIER or not settings.CAPITAL_COM_PASSWORD:
        return None
    try:
        svc = CapitalComService(demo=settings.CAPITAL_COM_DEMO)
        await svc.create_session()
        epic = CapitalComService.symbol_to_epic(symbol)
        if not epic:
            return None
        resolution = CapitalComService.timeframe_to_resolution(timeframe)
        data = await svc.get_historical_prices(epic, resolution, count)
        await svc.close()
        prices = data.get("prices", [])
        candles = []
        for p in prices:
            candles.append({
                "time": p.get("snapshotTime", ""),
                "open": (p.get("openPrice", {}).get("bid", 0) + p.get("openPrice", {}).get("ask", 0)) / 2,
                "high": (p.get("highPrice", {}).get("bid", 0) + p.get("highPrice", {}).get("ask", 0)) / 2,
                "low": (p.get("lowPrice", {}).get("bid", 0) + p.get("lowPrice", {}).get("ask", 0)) / 2,
                "close": (p.get("closePrice", {}).get("bid", 0) + p.get("closePrice", {}).get("ask", 0)) / 2,
                "volume": p.get("lastTradedVolume", 0),
            })
        return candles if candles else None
    except Exception as e:
        logger.debug(f"Capital.com candles fetch failed for {symbol}: {e}")
        return None


async def _fetch_candles_yfinance(symbol: str, timeframe: str, count: int) -> Optional[list]:
    """Fetch candles from Yahoo Finance as fallback."""
    ticker = YF_MAP.get(symbol)
    if not ticker:
        return None

    TF_YF = {
        "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
        "H1": "1h", "H4": "1h", "D1": "1d", "W1": "1wk",
    }
    TF_PERIOD = {
        "M1": "1d", "M5": "5d", "M15": "5d", "M30": "60d",
        "H1": "60d", "H4": "60d", "D1": "730d", "W1": "5y",
    }

    interval = TF_YF.get(timeframe.upper(), "1h")
    period = TF_PERIOD.get(timeframe.upper(), "60d")

    try:
        import yfinance as yf
        loop = asyncio.get_event_loop()
        hist = await loop.run_in_executor(
            None,
            lambda: yf.Ticker(ticker).history(period=period, interval=interval),
        )
        if hist.empty:
            return None
        hist = hist.tail(count)
        candles = []
        for ts, row in hist.iterrows():
            candles.append({
                "time": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row.get("Volume", 0)),
            })
        return candles
    except Exception as e:
        logger.debug(f"YFinance candle fetch failed for {symbol}: {e}")
        return None


def _generate_mock_candles(symbol: str, count: int) -> list:
    """Generate realistic mock OHLCV candles for demo."""
    import math
    base = _mock_price(symbol)
    candles = []
    price = base * 0.98
    now = datetime.now(timezone.utc).timestamp()

    for i in range(count):
        change = price * random.gauss(0, 0.003)
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + abs(price * random.uniform(0, 0.002))
        low_p = min(open_p, close_p) - abs(price * random.uniform(0, 0.002))
        volume = random.randint(50000, 200000)
        ts = datetime.utcfromtimestamp(now - (count - i) * 3600).isoformat()
        candles.append({
            "time": ts,
            "open": round(open_p, 5),
            "high": round(high_p, 5),
            "low": round(low_p, 5),
            "close": round(close_p, 5),
            "volume": volume,
        })
        price = close_p

    return candles


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/symbols")
async def get_symbols():
    """List all supported tradeable symbols."""
    return {
        "symbols": SUPPORTED_SYMBOLS,
        "count": len(SUPPORTED_SYMBOLS),
        "categories": {
            "metals": ["XAU/USD", "XAG/USD"],
            "energy": ["WTI/USD", "Brent/USD"],
            "forex_major": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "NZD/USD"],
            "forex_cross": ["EUR/GBP", "GBP/JPY", "EUR/JPY"],
            "indices": ["DXY"],
            "crypto": ["BTC/USD", "ETH/USD"],
        },
    }


@router.get("/price/{symbol:path}")
async def get_current_price(symbol: str):
    """Get current price for a symbol."""
    symbol = symbol.upper().replace("%2F", "/")
    if symbol not in SUPPORTED_SYMBOLS:
        return {"error": f"Symbol {symbol} not supported", "supported": SUPPORTED_SYMBOLS}
    price = await get_price(symbol)
    return {
        "symbol": symbol,
        "price": price,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/prices/all")
async def get_all_prices():
    """Get current prices for all symbols."""
    tasks = {symbol: get_price(symbol) for symbol in SUPPORTED_SYMBOLS}
    results = {}
    for symbol, coro in tasks.items():
        try:
            results[symbol] = await coro
        except Exception:
            results[symbol] = _mock_price(symbol)
    return {
        "prices": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
    }


@router.get("/candles/{symbol:path}")
async def get_candles(
    symbol: str,
    timeframe: str = Query(default="H1", description="Timeframe: M1, M5, M15, M30, H1, H4, D1, W1"),
    count: int = Query(default=200, ge=10, le=1000),
):
    """Get OHLCV candle data for a symbol."""
    symbol = symbol.upper().replace("%2F", "/")
    if symbol not in SUPPORTED_SYMBOLS:
        return {"error": f"Symbol {symbol} not supported"}

    candles = await _fetch_candles_capital(symbol, timeframe, count)
    if candles is None:
        candles = await _fetch_candles_yfinance(symbol, timeframe, count)
    if candles is None:
        candles = _generate_mock_candles(symbol, count)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(candles),
        "candles": candles,
    }


# ── WebSocket price streaming ─────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}  # symbol → [ws, ...]

    async def connect(self, ws: WebSocket, symbol: str):
        await ws.accept()
        self.active.setdefault(symbol, []).append(ws)
        logger.info(f"WS connected for {symbol}. Total: {len(self.active[symbol])}")

    def disconnect(self, ws: WebSocket, symbol: str):
        conns = self.active.get(symbol, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, symbol: str, data: dict):
        for ws in list(self.active.get(symbol, [])):
            try:
                await ws.send_json(data)
            except Exception:
                self.active[symbol].remove(ws)


ws_manager = ConnectionManager()


@router.websocket("/stream/{symbol:path}")
async def stream_prices(websocket: WebSocket, symbol: str):
    """Stream real-time prices for a symbol via WebSocket."""
    symbol = symbol.upper().replace("%2F", "/")
    if symbol not in SUPPORTED_SYMBOLS:
        await websocket.close(code=1008, reason="Unsupported symbol")
        return

    await ws_manager.connect(websocket, symbol)
    try:
        while True:
            price = await get_price(symbol)
            await websocket.send_json({
                "symbol": symbol,
                "price": price,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "price_update",
            })
            await asyncio.sleep(2)  # Stream every 2 seconds
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, symbol)
        logger.info(f"WS disconnected from {symbol}")
    except Exception as e:
        logger.error(f"WS error for {symbol}: {e}")
        ws_manager.disconnect(websocket, symbol)
