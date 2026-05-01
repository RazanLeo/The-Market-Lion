"""Market Data Service - Real-time price feed for The Market Lion."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List, Callable
import aiohttp
import websockets
from collections import defaultdict

logger = logging.getLogger(__name__)

SYMBOL_YAHOO_MAP = {
    "XAUUSD": "GC=F",
    "USOIL": "CL=F",
    "XBRUSD": "BZ=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "CAD=X",
    "USDCHF": "CHF=X",
    "NZDUSD": "NZDUSD=X",
    "DXY": "DX=F",
    "VIX": "^VIX",
    "SP500": "^GSPC",
    "BTCUSD": "BTC-USD",
}


class MarketDataService:
    def __init__(self):
        self.prices: Dict[str, Dict] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.running = False

    async def fetch_yahoo_quote(self, symbol: str) -> Optional[Dict]:
        yahoo_sym = SYMBOL_YAHOO_MAP.get(symbol, symbol)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval=1m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data.get("chart", {}).get("result", [{}])[0]
                        meta = result.get("meta", {})
                        indicators = result.get("indicators", {}).get("quote", [{}])[0]
                        closes = indicators.get("close", [None])
                        highs = indicators.get("high", [None])
                        lows = indicators.get("low", [None])
                        volumes = indicators.get("volume", [0])
                        valid_closes = [c for c in closes if c is not None]
                        if not valid_closes:
                            return None
                        return {
                            "symbol": symbol,
                            "bid": round(valid_closes[-1] * 0.9999, 5),
                            "ask": round(valid_closes[-1] * 1.0001, 5),
                            "price": round(valid_closes[-1], 5),
                            "high_24h": round(max(h for h in highs if h), 5),
                            "low_24h": round(min(l for l in lows if l), 5),
                            "volume": sum(v for v in volumes if v),
                            "change_pct": meta.get("regularMarketChangePercent", 0),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
        return None

    async def fetch_alpha_vantage_ohlcv(
        self, symbol: str, interval: str = "15min", api_key: str = "demo"
    ) -> Optional[List[Dict]]:
        func_map = {
            "1min": "TIME_SERIES_INTRADAY",
            "5min": "TIME_SERIES_INTRADAY",
            "15min": "TIME_SERIES_INTRADAY",
            "30min": "TIME_SERIES_INTRADAY",
            "60min": "TIME_SERIES_INTRADAY",
            "daily": "FX_DAILY",
        }
        av_sym = symbol.replace("USD", "").replace("EUR", "EUR/USD").replace("GBP", "GBP/USD")
        url = f"https://www.alphavantage.co/query?function={func_map.get(interval, 'TIME_SERIES_INTRADAY')}&symbol={av_sym}&interval={interval}&apikey={api_key}&outputsize=compact"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        key = f"Time Series ({interval})"
                        ts = data.get(key, {})
                        candles = []
                        for dt_str, vals in sorted(ts.items(), reverse=True)[:200]:
                            candles.append({
                                "timestamp": dt_str,
                                "open": float(vals.get("1. open", 0)),
                                "high": float(vals.get("2. high", 0)),
                                "low": float(vals.get("3. low", 0)),
                                "close": float(vals.get("4. close", 0)),
                                "volume": float(vals.get("5. volume", 1000)),
                            })
                        return list(reversed(candles))
        except Exception as e:
            logger.warning(f"Alpha Vantage error for {symbol}: {e}")
        return None

    async def get_ohlcv_dataframe(self, symbol: str, timeframe: str = "M15"):
        import pandas as pd
        interval_map = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "60min", "H4": "daily", "D1": "daily"}
        interval = interval_map.get(timeframe, "15min")
        candles = await self.fetch_alpha_vantage_ohlcv(symbol, interval)
        if candles:
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            return df
        return self._generate_synthetic_data(symbol, 200)

    def _generate_synthetic_data(self, symbol: str, bars: int = 200):
        """Generate synthetic data for testing when API is unavailable."""
        import pandas as pd
        import numpy as np
        base_prices = {
            "XAUUSD": 2350.0, "USOIL": 78.0, "EURUSD": 1.085,
            "GBPUSD": 1.265, "USDJPY": 149.5, "AUDUSD": 0.655,
        }
        base = base_prices.get(symbol, 1.0)
        np.random.seed(42)
        changes = np.random.normal(0, base * 0.002, bars)
        closes = base + np.cumsum(changes)
        opens = np.roll(closes, 1)
        opens[0] = closes[0]
        highs = np.maximum(closes, opens) + np.abs(np.random.normal(0, base * 0.001, bars))
        lows = np.minimum(closes, opens) - np.abs(np.random.normal(0, base * 0.001, bars))
        volumes = np.random.uniform(1000, 10000, bars)
        idx = pd.date_range(end=pd.Timestamp.now(), periods=bars, freq="15min")
        return pd.DataFrame({
            "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes
        }, index=idx)

    async def stream_prices(self, symbols: List[str], interval_sec: int = 5):
        self.running = True
        while self.running:
            for sym in symbols:
                quote = await self.fetch_yahoo_quote(sym)
                if quote:
                    self.prices[sym] = quote
                    for cb in self.subscribers.get(sym, []):
                        await cb(quote)
            await asyncio.sleep(interval_sec)

    def subscribe(self, symbol: str, callback: Callable):
        self.subscribers[symbol].append(callback)

    def stop(self):
        self.running = False
