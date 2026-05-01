"""Market Lion — Order Execution Service.

Supports: Capital.com REST, MetaApi (MT5/MT4), Exness.
All broker credentials are stored AES-256 encrypted in PostgreSQL.
"""
import asyncio
import os
import logging
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import aiohttp
import asyncpg
import redis.asyncio as aioredis
from cryptography.fernet import Fernet

logger = logging.getLogger("order-executor")


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


@dataclass
class OrderRequest:
    user_id: str
    broker_connection_id: str
    symbol: str
    side: OrderSide
    lot_size: float
    entry_price: Optional[float] = None
    sl_price: Optional[float] = None
    tp1_price: Optional[float] = None
    tp2_price: Optional[float] = None
    tp3_price: Optional[float] = None
    order_type: OrderType = OrderType.MARKET
    comment: str = "أسد السوق"
    magic_number: int = 202400


@dataclass
class OrderResult:
    success: bool
    broker: str
    ticket: Optional[str] = None
    error: Optional[str] = None
    fill_price: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ──────────────────────────────────────────────
# Encryption helpers
# ──────────────────────────────────────────────
_fernet: Optional[Fernet] = None

def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = os.getenv("ENCRYPTION_KEY", "")
        if not key:
            key = Fernet.generate_key().decode()
            logger.warning("No ENCRYPTION_KEY set — using ephemeral key (not suitable for production)")
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def decrypt_creds(encrypted: str) -> dict:
    import json
    return json.loads(get_fernet().decrypt(encrypted.encode()).decode())


def encrypt_creds(creds: dict) -> str:
    import json
    return get_fernet().encrypt(json.dumps(creds).encode()).decode()


# ──────────────────────────────────────────────
# Capital.com Broker
# ──────────────────────────────────────────────
class CapitalComBroker:
    BASE_URL = "https://api-capital.backend-capital.com/api/v1"
    DEMO_URL = "https://demo-api-capital.backend-capital.com/api/v1"

    def __init__(self, api_key: str, password: str, is_demo: bool = True):
        self.api_key = api_key
        self.password = password
        self.is_demo = is_demo
        self.base = self.DEMO_URL if is_demo else self.BASE_URL
        self._session_token: Optional[str] = None
        self._cst_token: Optional[str] = None

    async def _authenticate(self):
        async with aiohttp.ClientSession() as sess:
            resp = await sess.post(
                f"{self.base}/session",
                json={"identifier": self.api_key, "password": self.password},
                headers={"X-CAP-API-KEY": self.api_key}
            )
            if resp.status == 200:
                headers = resp.headers
                self._cst_token = headers.get("CST")
                self._session_token = headers.get("X-SECURITY-TOKEN")
                logger.info("Capital.com authenticated")
            else:
                text = await resp.text()
                raise Exception(f"Capital.com auth failed: {text}")

    def _headers(self):
        return {
            "X-SECURITY-TOKEN": self._session_token or "",
            "CST": self._cst_token or "",
            "Content-Type": "application/json",
        }

    async def place_order(self, req: OrderRequest) -> OrderResult:
        try:
            await self._authenticate()
            direction = "BUY" if req.side == OrderSide.BUY else "SELL"
            payload = {
                "epic": req.symbol,
                "direction": direction,
                "size": str(req.lot_size),
                "guaranteedStop": False,
            }
            if req.sl_price:
                payload["stopLevel"] = req.sl_price
            if req.tp1_price:
                payload["profitLevel"] = req.tp1_price

            async with aiohttp.ClientSession() as sess:
                resp = await sess.post(
                    f"{self.base}/positions",
                    json=payload,
                    headers=self._headers()
                )
                data = await resp.json()
                if resp.status in (200, 201) and data.get("dealStatus") == "ACCEPTED":
                    return OrderResult(
                        success=True, broker="capital_com",
                        ticket=data.get("dealReference"),
                        fill_price=float(data.get("level", 0))
                    )
                return OrderResult(success=False, broker="capital_com", error=str(data))
        except Exception as e:
            return OrderResult(success=False, broker="capital_com", error=str(e))

    async def close_position(self, deal_id: str) -> bool:
        try:
            await self._authenticate()
            async with aiohttp.ClientSession() as sess:
                resp = await sess.delete(f"{self.base}/positions/{deal_id}", headers=self._headers())
                return resp.status == 200
        except Exception:
            return False


# ──────────────────────────────────────────────
# MetaApi (MT4/MT5)
# ──────────────────────────────────────────────
class MetaApiBroker:
    def __init__(self, token: str, account_id: str):
        self.token = token
        self.account_id = account_id
        self.base = "https://mt-client-api-v1.new-york.agiliumtrade.ai"

    def _headers(self):
        return {"auth-token": self.token, "Content-Type": "application/json"}

    async def place_order(self, req: OrderRequest) -> OrderResult:
        try:
            action = "ORDER_TYPE_BUY" if req.side == OrderSide.BUY else "ORDER_TYPE_SELL"
            payload = {
                "actionType": action,
                "symbol": req.symbol,
                "volume": req.lot_size,
                "magic": req.magic_number,
                "comment": req.comment,
            }
            if req.sl_price:
                payload["stopLoss"] = req.sl_price
            if req.tp1_price:
                payload["takeProfit"] = req.tp1_price

            async with aiohttp.ClientSession() as sess:
                url = f"{self.base}/users/current/accounts/{self.account_id}/trade"
                resp = await sess.post(url, json=payload, headers=self._headers())
                data = await resp.json()

                if resp.status == 200 and data.get("numericCode") in (0, 10009):
                    return OrderResult(
                        success=True, broker="mt5_metaapi",
                        ticket=str(data.get("orderId") or data.get("positionId")),
                    )
                return OrderResult(success=False, broker="mt5_metaapi", error=str(data))
        except Exception as e:
            return OrderResult(success=False, broker="mt5_metaapi", error=str(e))

    async def get_account_info(self) -> dict:
        async with aiohttp.ClientSession() as sess:
            url = f"{self.base}/users/current/accounts/{self.account_id}/account-information"
            resp = await sess.get(url, headers=self._headers())
            return await resp.json()


# ──────────────────────────────────────────────
# Order Execution Manager
# ──────────────────────────────────────────────
class OrderExecutionManager:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._redis: Optional[aioredis.Redis] = None

    async def init(self):
        self._pool = await asyncpg.create_pool(
            os.getenv("POSTGRES_URL", "postgresql://lion:lion_secret_2024@localhost:5432/market_lion")
        )
        self._redis = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
        )

    async def _get_broker(self, connection_id: str):
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT broker, encrypted_creds, meta_api_id, is_demo FROM broker_connections WHERE id=$1 AND is_active=TRUE",
                connection_id
            )
        if not row:
            raise ValueError("Broker connection not found")

        creds = decrypt_creds(row["encrypted_creds"])
        broker = row["broker"]

        if broker == "capital_com":
            return CapitalComBroker(creds["api_key"], creds["password"], row["is_demo"])
        elif broker in ("mt5", "mt4", "exness", "icmarkets"):
            return MetaApiBroker(os.getenv("METAAPI_TOKEN", ""), row["meta_api_id"])
        else:
            raise ValueError(f"Unsupported broker: {broker}")

    async def execute_order(self, req: OrderRequest) -> OrderResult:
        # Circuit breaker check
        cb_key = f"circuit_breaker:{req.user_id}"
        if await self._redis.exists(cb_key):
            ttl = await self._redis.ttl(cb_key)
            return OrderResult(
                success=False, broker="system",
                error=f"قاطع الدائرة نشط — انتظر {ttl // 60} دقيقة"
            )

        try:
            broker = await self._get_broker(req.broker_connection_id)
            result = await broker.place_order(req)

            if result.success:
                await self._save_trade(req, result)
                logger.info(f"Order executed: {req.symbol} {req.side} {req.lot_size} — ticket {result.ticket}")
            else:
                logger.error(f"Order failed: {result.error}")

            return result
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return OrderResult(success=False, broker="unknown", error=str(e))

    async def _save_trade(self, req: OrderRequest, result: OrderResult):
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO trades (user_id, broker, broker_ticket, symbol, side, entry_price,
                   sl_price, tp1_price, tp2_price, tp3_price, lot_size, status)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'open')""",
                req.user_id, result.broker, result.ticket, req.symbol,
                req.side.value, result.fill_price or req.entry_price,
                req.sl_price, req.tp1_price, req.tp2_price, req.tp3_price, req.lot_size
            )

    async def close_trade(self, trade_id: str, reason: str = "manual"):
        async with self._pool.acquire() as conn:
            trade = await conn.fetchrow(
                "SELECT * FROM trades WHERE id=$1 AND status='open'", trade_id
            )
            if not trade:
                return {"error": "Trade not found"}

            conn_row = await conn.fetchrow(
                "SELECT id FROM broker_connections WHERE user_id=$1 AND broker=$2 AND is_active=TRUE",
                trade["user_id"], trade["broker"]
            )
            if conn_row:
                broker = await self._get_broker(str(conn_row["id"]))
                if isinstance(broker, CapitalComBroker):
                    await broker.close_position(trade["broker_ticket"])

            await conn.execute(
                "UPDATE trades SET status='closed', close_reason=$1, closed_at=NOW() WHERE id=$2",
                reason, trade_id
            )
        return {"success": True}


executor_mgr = OrderExecutionManager()


async def main():
    await executor_mgr.init()
    logger.info("Order Execution Service ready")
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
