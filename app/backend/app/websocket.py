"""WebSocket endpoints — broadcasts confluence + signals + news."""
from __future__ import annotations
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
import redis.asyncio as aioredis

from .core.config import settings
from .core.security import decode_token

router = APIRouter()


@router.websocket("/analysis")
async def ws_analysis(ws: WebSocket, token: str = Query(...), symbol: str = Query(...), tf: str = Query("15M")):
    data = decode_token(token)
    if not data or data.get("type") != "access":
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await ws.accept()
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    channel = f"analysis:{symbol}:{tf}"
    await pubsub.subscribe(channel)
    try:
        # Send a hello
        await ws.send_json({"type": "hello", "symbol": symbol, "tf": tf})
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("type") == "message":
                payload = msg["data"]
                if isinstance(payload, str):
                    try: payload = json.loads(payload)
                    except Exception: pass
                await ws.send_json(payload)
            else:
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis.close()


@router.websocket("/news")
async def ws_news(ws: WebSocket, token: str = Query(...)):
    data = decode_token(token)
    if not data or data.get("type") != "access":
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await ws.accept()
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe("news:global")
    try:
        await ws.send_json({"type": "hello", "channel": "news:global"})
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("type") == "message":
                await ws.send_json(json.loads(msg["data"]) if isinstance(msg["data"], str) else msg["data"])
            else:
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe("news:global")
        await pubsub.close()
        await redis.close()
