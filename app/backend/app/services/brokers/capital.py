"""Capital.com REST + Streaming Adapter.

Docs: https://open-api.capital.com/

Auth flow:
  POST /api/v1/session  with X-CAP-API-KEY, identifier, encryptedPassword=false, password
  → returns CST + X-SECURITY-TOKEN headers used in subsequent requests.

Endpoints used:
  - /api/v1/accounts         (list accounts + balance)
  - /api/v1/positions        (open + list + close)
  - /api/v1/positions/{id}   (modify SL/TP)
  - /api/v1/markets          (instrument data)
  - /api/v1/prices/{epic}    (historical prices)
  - WebSocket streaming for live prices.
"""
from __future__ import annotations

import asyncio
import json
import time
from decimal import Decimal
from typing import Any, AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ...core.config import settings
from ...core.logging import get_logger

log = get_logger("capital")


class CapitalAdapter:
    def __init__(self, demo: bool = True, timeout: float = 15.0):
        self.base = settings.CAPITAL_DEMO_BASE_URL if demo else settings.CAPITAL_BASE_URL
        self.stream_base = settings.CAPITAL_STREAM_URL
        self._client = httpx.AsyncClient(base_url=self.base, timeout=timeout)
        self._cst: str | None = None
        self._x_sec: str | None = None
        self._account_id: str | None = None
        self._api_key: str | None = None

    async def close(self) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4), retry=retry_if_exception_type(httpx.HTTPError))
    async def create_session(self, *, api_key: str, identifier: str, password: str) -> dict[str, Any]:
        self._api_key = api_key
        r = await self._client.post(
            "/api/v1/session",
            headers={"X-CAP-API-KEY": api_key, "Content-Type": "application/json"},
            json={"identifier": identifier, "password": password, "encryptedPassword": False},
        )
        r.raise_for_status()
        self._cst = r.headers.get("CST")
        self._x_sec = r.headers.get("X-SECURITY-TOKEN")
        body = r.json()
        # current account
        accounts = (body.get("accounts") or [])
        primary = next((a for a in accounts if a.get("preferred")), accounts[0] if accounts else None)
        self._account_id = (primary or {}).get("accountId")
        log.info("capital_login_ok", account=self._account_id)
        return body

    def _headers(self) -> dict[str, str]:
        return {
            "X-CAP-API-KEY": self._api_key or "",
            "CST": self._cst or "",
            "X-SECURITY-TOKEN": self._x_sec or "",
            "Content-Type": "application/json",
        }

    async def account_info(self) -> dict[str, Any]:
        r = await self._client.get("/api/v1/accounts", headers=self._headers())
        r.raise_for_status()
        body = r.json()
        accts = body.get("accounts") or []
        primary = next((a for a in accts if a.get("accountId") == self._account_id), accts[0] if accts else {})
        bal = primary.get("balance", {}) or {}
        return {
            "account_id": primary.get("accountId"),
            "currency": primary.get("currency"),
            "balance": float(bal.get("balance") or 0),
            "available": float(bal.get("available") or 0),
            "deposit": float(bal.get("deposit") or 0),
            "profit_loss": float(bal.get("profitLoss") or 0),
            "type": primary.get("accountType"),
        }

    async def positions(self) -> list[dict[str, Any]]:
        r = await self._client.get("/api/v1/positions", headers=self._headers())
        r.raise_for_status()
        return r.json().get("positions", [])

    async def market_info(self, epic: str) -> dict[str, Any]:
        r = await self._client.get(f"/api/v1/markets/{epic}", headers=self._headers())
        r.raise_for_status()
        return r.json()

    async def historical_prices(self, epic: str, resolution: str = "MINUTE_15", max_bars: int = 200) -> list[dict[str, Any]]:
        r = await self._client.get(
            f"/api/v1/prices/{epic}",
            headers=self._headers(),
            params={"resolution": resolution, "max": max_bars},
        )
        r.raise_for_status()
        return r.json().get("prices", [])

    async def open_market(
        self,
        symbol: str,
        side: str,
        lot: float,
        sl: float | None = None,
        tp: float | None = None,
    ) -> dict[str, Any]:
        epic = self._symbol_to_epic(symbol)
        body = {
            "epic": epic,
            "direction": "BUY" if side == "buy" else "SELL",
            "size": lot,
            "guaranteedStop": False,
            "trailingStop": False,
        }
        if sl is not None: body["stopLevel"] = sl
        if tp is not None: body["profitLevel"] = tp
        r = await self._client.post("/api/v1/positions", headers=self._headers(), json=body)
        if r.status_code >= 400:
            log.error("capital_open_failed", status=r.status_code, body=r.text)
        r.raise_for_status()
        return r.json()

    async def close_position(self, deal_id: str) -> dict[str, Any]:
        r = await self._client.delete(f"/api/v1/positions/{deal_id}", headers=self._headers())
        r.raise_for_status()
        return r.json()

    async def modify_position(self, deal_id: str, *, sl: float | None = None, tp: float | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if sl is not None: body["stopLevel"] = sl
        if tp is not None: body["profitLevel"] = tp
        r = await self._client.put(f"/api/v1/positions/{deal_id}", headers=self._headers(), json=body)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _symbol_to_epic(symbol: str) -> str:
        # Capital.com epic mapping (representative). Update from /markets search at runtime ideally.
        m = {
            "XAUUSD": "GOLD",
            "XAGUSD": "SILVER",
            "USOIL": "OIL_CRUDE",
            "BRENT": "OIL_BRENT",
            "EURUSD": "EURUSD",
            "GBPUSD": "GBPUSD",
            "USDJPY": "USDJPY",
            "USDCHF": "USDCHF",
            "AUDUSD": "AUDUSD",
            "NZDUSD": "NZDUSD",
            "USDCAD": "USDCAD",
            "DXY": "DXY",
        }
        return m.get(symbol.upper(), symbol.upper())

    # ── Streaming via SSE/WebSocket ─────────────────────────────────
    async def stream_prices(self, symbols: list[str]) -> AsyncIterator[dict[str, Any]]:
        """Streams price updates via Capital.com WebSocket bridge.

        Capital.com offers REST polling + a streaming endpoint. For initial implementation,
        we poll /prices/{epic} every second. Switch to native WS when partner credentials granted.
        """
        epics = [self._symbol_to_epic(s) for s in symbols]
        while True:
            for sym, epic in zip(symbols, epics):
                try:
                    r = await self._client.get(f"/api/v1/prices/{epic}", headers=self._headers(), params={"resolution": "MINUTE", "max": 1})
                    if r.status_code == 200:
                        prices = r.json().get("prices", [])
                        if prices:
                            p = prices[-1]
                            yield {
                                "symbol": sym,
                                "ts": p.get("snapshotTimeUTC"),
                                "bid": float(p.get("closePrice", {}).get("bid", 0)),
                                "ask": float(p.get("closePrice", {}).get("ask", 0)),
                            }
                except Exception as e:
                    log.warning("stream_poll_err", err=str(e))
            await asyncio.sleep(1.0)
