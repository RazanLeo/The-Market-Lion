"""FastAPI entrypoint — wires routers, middleware, lifecycle."""
from __future__ import annotations

from contextlib import asynccontextmanager
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration

from . import __version__
from .core.config import settings
from .core.logging import configure_logging, get_logger
from .routers import (
    auth as auth_router,
    users as users_router,
    subscriptions as sub_router,
    payments as pay_router,
    broker_links as broker_router,
    analysis as analysis_router,
    signals as signals_router,
    positions as pos_router,
    admin as admin_router,
    chat as chat_router,
    webhooks as webhooks_router,
    health as health_router,
    market as market_router,
    support as support_router,
)
from .websocket import router as ws_router

configure_logging()
log = get_logger("app.main")

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
        integrations=[FastApiIntegration()],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", env=settings.APP_ENV, version=__version__)
    yield
    log.info("shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.APP_ENV != "production" else None,
)

origins = [settings.APP_URL, "http://localhost:3000", "http://localhost:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(Exception)
async def unhandled_exc(request: Request, exc: Exception):
    log.error("unhandled_exception", err=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={"ok": False, "error": "internal_error"})


# ── route prefixes ────────────────────────────────────────────────
api = "/api/v1"
app.include_router(health_router.router, prefix="")
app.include_router(auth_router.router, prefix=f"{api}/auth", tags=["auth"])
app.include_router(users_router.router, prefix=f"{api}/users", tags=["users"])
app.include_router(sub_router.router, prefix=f"{api}/subscriptions", tags=["subscriptions"])
app.include_router(pay_router.router, prefix=f"{api}/payments", tags=["payments"])
app.include_router(broker_router.router, prefix=f"{api}/broker-links", tags=["broker"])
app.include_router(analysis_router.router, prefix=f"{api}/analysis", tags=["analysis"])
app.include_router(signals_router.router, prefix=f"{api}/signals", tags=["signals"])
app.include_router(pos_router.router, prefix=f"{api}/trades", tags=["trades"])
app.include_router(chat_router.router, prefix=f"{api}/chat", tags=["chat"])
app.include_router(admin_router.router, prefix=f"{api}/admin", tags=["admin"])
app.include_router(webhooks_router.router, prefix=f"{api}/webhooks", tags=["webhooks"])
app.include_router(market_router.router, prefix=f"{api}/market", tags=["market"])
app.include_router(support_router.router, prefix=f"{api}/support", tags=["support"])
app.include_router(ws_router, prefix="/ws", tags=["ws"])
