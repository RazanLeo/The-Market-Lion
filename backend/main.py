"""
أسد السوق / The Market Lion — FastAPI Backend
Run: uvicorn main:app --reload
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import create_tables, engine, AsyncSessionLocal
from auth import get_user_from_ws_token

# Routers
from routers.auth import router as auth_router
from routers.market_data import router as market_router
from routers.technical import router as technical_router
from routers.fundamental import router as fundamental_router
from routers.broker import router as broker_router
from routers.bot import router as bot_router
from routers.subscription import router as subscription_router
from routers.admin import router as admin_router
from routers.ai_chat import router as ai_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("market-lion")

# ── Per-user WebSocket registry ───────────────────────────────────────────────
# user_id (str) → WebSocket
ws_connections: dict[str, WebSocket] = {}

# ── Optional Redis client ─────────────────────────────────────────────────────
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    global redis_client

    logger.info("Starting Market Lion API...")

    # 1. Create DB tables
    try:
        await create_tables()
        logger.info("Database tables ready")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        logger.warning("Continuing without DB — some endpoints will fail")

    # 2. Connect to Redis (optional)
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await redis_client.ping()
        logger.info("Redis connected")
    except Exception as e:
        redis_client = None
        logger.warning(f"Redis unavailable ({e}) — caching disabled")

    logger.info(
        f"Market Lion API ready | env={settings.ENVIRONMENT} | debug={settings.DEBUG}"
    )

    yield  # ← Application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down Market Lion API...")

    # Close active WebSocket connections
    for ws in list(ws_connections.values()):
        try:
            await ws.close()
        except Exception:
            pass
    ws_connections.clear()

    # Close Redis
    if redis_client:
        try:
            await redis_client.aclose()
        except Exception:
            pass

    # Dispose DB engine
    await engine.dispose()
    logger.info("Shutdown complete")


# ── FastAPI Application ────────────────────────────────────────────────────────

app = FastAPI(
    title="أسد السوق / The Market Lion API",
    description=(
        "AI-powered trading platform. "
        "Multi-school technical analysis, broker integration (Capital.com / Exness / MT5), "
        "automated trading bot, WebSocket streaming, and Arabic-first AI chat."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── API Routers ───────────────────────────────────────────────────────────────

app.include_router(auth_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(technical_router, prefix="/api")
app.include_router(fundamental_router, prefix="/api")
app.include_router(broker_router, prefix="/api")
app.include_router(bot_router, prefix="/api")
app.include_router(subscription_router, prefix="/api/subscription", tags=["Subscription"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI Chat"])

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check for load balancers / monitoring."""
    db_ok = False
    redis_ok = False

    # DB check
    try:
        import sqlalchemy
        async with AsyncSessionLocal() as session:
            await session.execute(sqlalchemy.text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Redis check
    if redis_client:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": "up" if db_ok else "down",
            "redis": "up" if redis_ok else "unavailable",
            "openai": "configured" if settings.OPENAI_API_KEY else "not_configured",
            "capital_com": "configured" if settings.CAPITAL_COM_IDENTIFIER else "not_configured",
            "news_api": "configured" if settings.NEWS_API_KEY else "not_configured",
        },
        "active_ws_connections": len(ws_connections),
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "أسد السوق / The Market Lion API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "websocket": "/ws/{token}",
        "description": "AI-powered multi-school trading platform",
    }


# ── Main WebSocket endpoint ───────────────────────────────────────────────────

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Authenticated WebSocket for real-time push notifications.

    Connect: ws://host/ws/<access_token>

    Incoming message types (from client):
      {"type": "ping"}
      {"type": "subscribe_symbol", "symbol": "XAU/USD"}
      {"type": "unsubscribe_symbol", "symbol": "XAU/USD"}

    Outgoing message types (from server):
      {"type": "connected", ...}
      {"type": "pong"}
      {"type": "ping"}
      {"type": "signal", "data": {...}}
      {"type": "price_update", "symbol": "...", "price": ...}
      {"type": "alert", "message": "..."}
    """
    # Validate token before accepting
    async with AsyncSessionLocal() as db:
        user = await get_user_from_ws_token(token, db)

    if not user:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    await websocket.accept()
    user_id = str(user.id)

    # Register connection (newest wins)
    if user_id in ws_connections:
        try:
            await ws_connections[user_id].close(code=4002, reason="New connection opened")
        except Exception:
            pass
    ws_connections[user_id] = websocket

    logger.info(f"WS connected: user={user.email}")

    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"مرحباً {user.full_name or user.email}! اتصال WebSocket ناجح.",
            "user_id": user_id,
            "subscription_tier": user.subscription_tier,
        })

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0,
                )
                msg_type = data.get("type", "")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "subscribe_symbol":
                    symbol = data.get("symbol", "")
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbol": symbol,
                        "message": f"Subscribed to {symbol} updates",
                    })

                elif msg_type == "unsubscribe_symbol":
                    symbol = data.get("symbol", "")
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "symbol": symbol,
                    })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    })

            except asyncio.TimeoutError:
                # Keep alive
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: user={user.email}")
    except Exception as e:
        logger.error(f"WS error for {user.email}: {e}")
    finally:
        ws_connections.pop(user_id, None)


# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "path": str(request.url.path),
            "docs": "/docs",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
