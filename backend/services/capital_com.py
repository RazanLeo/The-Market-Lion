"""Capital.com REST API service."""
import logging
from typing import Optional
import httpx

from config import settings

logger = logging.getLogger(__name__)

# Symbol mapping: platform name → Capital.com epic
SYMBOL_MAP = {
    "XAU/USD": "GOLD",
    "XAG/USD": "SILVER",
    "WTI/USD": "OIL_CRUDE",
    "Brent/USD": "OIL_BRENT",
    "EUR/USD": "EURUSD",
    "GBP/USD": "GBPUSD",
    "USD/JPY": "USDJPY",
    "AUD/USD": "AUDUSD",
    "USD/CAD": "USDCAD",
    "NZD/USD": "NZDUSD",
    "EUR/GBP": "EURGBP",
    "GBP/JPY": "GBPJPY",
    "EUR/JPY": "EURJPY",
    "DXY": "DXY",
    "BTC/USD": "BITCOIN",
    "ETH/USD": "ETHEREUM",
}

REVERSE_SYMBOL_MAP = {v: k for k, v in SYMBOL_MAP.items()}

# Timeframe mapping
TIMEFRAME_MAP = {
    "M1": "MINUTE",
    "M5": "MINUTE_5",
    "M15": "MINUTE_15",
    "M30": "MINUTE_30",
    "H1": "HOUR",
    "H4": "HOUR_4",
    "D1": "DAY",
    "W1": "WEEK",
}


class CapitalComService:
    BASE_URL_DEMO = "https://demo-api-capital.backend-capital.com/api/v1"
    BASE_URL_LIVE = "https://api-capital.backend-capital.com/api/v1"

    def __init__(
        self,
        identifier: Optional[str] = None,
        password: Optional[str] = None,
        demo: bool = True,
    ):
        self.identifier = identifier or settings.CAPITAL_COM_IDENTIFIER
        self.password = password or settings.CAPITAL_COM_PASSWORD
        self.demo = demo
        self.base_url = self.BASE_URL_DEMO if demo else self.BASE_URL_LIVE
        self._cst: Optional[str] = None
        self._security_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._cst:
            h["CST"] = self._cst
        if self._security_token:
            h["X-SECURITY-TOKEN"] = self._security_token
        return h

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Session ──────────────────────────────────────────────────────────────

    async def create_session(
        self,
        identifier: Optional[str] = None,
        password: Optional[str] = None,
        demo: Optional[bool] = None,
    ) -> dict:
        """Create a new Capital.com session. Returns session info."""
        ident = identifier or self.identifier
        pwd = password or self.password
        if demo is not None:
            self.demo = demo
            self.base_url = self.BASE_URL_DEMO if demo else self.BASE_URL_LIVE

        if not ident or not pwd:
            raise ValueError("Capital.com identifier and password are required")

        client = await self._get_client()
        resp = await client.post(
            f"{self.base_url}/session",
            json={"identifier": ident, "password": pwd, "encryptedPassword": False},
        )
        resp.raise_for_status()
        self._cst = resp.headers.get("CST")
        self._security_token = resp.headers.get("X-SECURITY-TOKEN")
        return resp.json()

    async def _ensure_session(self):
        if not self._cst or not self._security_token:
            await self.create_session()

    # ── Account ──────────────────────────────────────────────────────────────

    async def get_account_details(self) -> dict:
        await self._ensure_session()
        client = await self._get_client()
        resp = await client.get(
            f"{self.base_url}/accounts", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    async def get_account_preferences(self) -> dict:
        await self._ensure_session()
        client = await self._get_client()
        resp = await client.get(
            f"{self.base_url}/accounts/preferences", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    # ── Positions ────────────────────────────────────────────────────────────

    async def get_positions(self) -> dict:
        await self._ensure_session()
        client = await self._get_client()
        resp = await client.get(
            f"{self.base_url}/positions", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    async def close_position(self, deal_id: str) -> dict:
        await self._ensure_session()
        client = await self._get_client()
        resp = await client.delete(
            f"{self.base_url}/positions/{deal_id}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    # ── Orders ───────────────────────────────────────────────────────────────

    async def create_order(
        self,
        epic: str,
        direction: str,  # "BUY" | "SELL"
        size: float,
        stop_level: Optional[float] = None,
        profit_level: Optional[float] = None,
        order_type: str = "MARKET",
        level: Optional[float] = None,
    ) -> dict:
        await self._ensure_session()
        payload: dict = {
            "epic": epic,
            "direction": direction.upper(),
            "size": size,
            "orderType": order_type,
            "guaranteedStop": False,
            "trailingStop": False,
        }
        if stop_level:
            payload["stopLevel"] = stop_level
        if profit_level:
            payload["profitLevel"] = profit_level
        if level and order_type != "MARKET":
            payload["level"] = level

        client = await self._get_client()
        resp = await client.post(
            f"{self.base_url}/positions", headers=self._headers, json=payload
        )
        resp.raise_for_status()
        return resp.json()

    async def cancel_order(self, order_id: str) -> dict:
        await self._ensure_session()
        client = await self._get_client()
        resp = await client.delete(
            f"{self.base_url}/workingorders/{order_id}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    # ── Market data ──────────────────────────────────────────────────────────

    async def get_market_prices(self, epic: str) -> dict:
        """Get current bid/ask for an epic."""
        await self._ensure_session()
        client = await self._get_client()
        resp = await client.get(
            f"{self.base_url}/markets/{epic}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    async def get_historical_prices(
        self,
        epic: str,
        resolution: str = "HOUR",
        max_results: int = 200,
    ) -> dict:
        """Fetch historical OHLCV candles."""
        await self._ensure_session()
        client = await self._get_client()
        resp = await client.get(
            f"{self.base_url}/prices/{epic}",
            headers=self._headers,
            params={"resolution": resolution, "max": max_results},
        )
        resp.raise_for_status()
        return resp.json()

    async def search_markets(self, search_term: str) -> dict:
        """Search for tradeable markets."""
        await self._ensure_session()
        client = await self._get_client()
        resp = await client.get(
            f"{self.base_url}/markets",
            headers=self._headers,
            params={"searchTerm": search_term},
        )
        resp.raise_for_status()
        return resp.json()

    # ── Utilities ────────────────────────────────────────────────────────────

    @staticmethod
    def symbol_to_epic(symbol: str) -> Optional[str]:
        return SYMBOL_MAP.get(symbol)

    @staticmethod
    def epic_to_symbol(epic: str) -> Optional[str]:
        return REVERSE_SYMBOL_MAP.get(epic)

    @staticmethod
    def timeframe_to_resolution(timeframe: str) -> str:
        return TIMEFRAME_MAP.get(timeframe.upper(), "HOUR")
