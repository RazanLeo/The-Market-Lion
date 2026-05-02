"""WebSocket router — real-time price & signal streaming."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt

from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Connected clients: {user_id: [ws1, ws2, ...]}
_connections: dict[str, list[WebSocket]] = {}


async def broadcast(user_id: Optional[str], data: dict):
    """Send data to specific user or all users if user_id is None."""
    msg = json.dumps(data, ensure_ascii=False, default=str)
    if user_id:
        for ws in _connections.get(user_id, []):
            try:
                await ws.send_text(msg)
            except Exception:
                pass
    else:
        for connections in _connections.values():
            for ws in connections:
                try:
                    await ws.send_text(msg)
                except Exception:
                    pass


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()
    user_id = None

    # Verify token
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        await websocket.send_text(json.dumps({"type": "error", "message": "Invalid token"}))
        await websocket.close()
        return

    # Register connection
    if user_id not in _connections:
        _connections[user_id] = []
    _connections[user_id].append(websocket)
    logger.info(f"WS connected: user {user_id}")

    try:
        # Send welcome
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "مرحباً في أسد السوق",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

        # Keep alive + send periodic mock prices
        counter = 0
        while True:
            await asyncio.sleep(5)
            counter += 1

            # Every 5 seconds: send price update
            await websocket.send_text(json.dumps({
                "type": "price_update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prices": {
                    "XAU/USD": {"price": 2345.60 + (counter % 10) * 0.5, "change": 0.45, "change_pct": 0.019},
                    "EUR/USD": {"price": 1.0852, "change": -0.0003, "change_pct": -0.028},
                    "WTI/USD": {"price": 78.45, "change": 0.23, "change_pct": 0.294},
                    "BTC/USD": {"price": 67800 + (counter % 5) * 100, "change": 250, "change_pct": 0.37},
                },
            }))

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: user {user_id}")
    except Exception as e:
        logger.error(f"WS error: {e}")
    finally:
        if user_id and websocket in _connections.get(user_id, []):
            _connections[user_id].remove(websocket)
