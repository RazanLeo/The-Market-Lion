"""Trading bot router: start/stop, signals, performance."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth import get_current_user
from models.user import User
from services.technical_analysis import ta_service
from routers.market_data import get_candles, SUPPORTED_SYMBOLS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bot", tags=["Trading Bot"])

CONFLUENCE_THRESHOLD = 0.75

# In-memory bot state per user
# {user_id: {"running": bool, "mode": str, "symbols": [...], "task": asyncio.Task}}
_bot_state: dict[str, dict] = {}

# Signal history per user (in-memory, last 100)
_signals: dict[str, list] = {}


# ── Schemas ───────────────────────────────────────────────────────────────────

class BotStartRequest(BaseModel):
    mode: str = "manual"  # "auto" | "semi_auto" | "manual"
    symbols: list[str] = ["XAU/USD", "EUR/USD", "BTC/USD"]
    timeframe: str = "H1"
    scan_interval_seconds: int = 60


class SignalOut(BaseModel):
    symbol: str
    signal: str
    confluence_score: float
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    trend: str
    timeframe: str
    timestamp: str
    executed: bool = False


# ── Bot scanning loop ─────────────────────────────────────────────────────────

async def _bot_loop(user_id: str, mode: str, symbols: list[str], timeframe: str, interval: int):
    """Background task that scans symbols and emits signals."""
    logger.info(f"Bot started for user {user_id} | mode={mode} symbols={symbols}")
    while True:
        state = _bot_state.get(user_id)
        if not state or not state.get("running"):
            break

        for symbol in symbols:
            try:
                candle_resp = await get_candles(symbol, timeframe=timeframe, count=200)
                candles = candle_resp.get("candles", [])
                if not candles:
                    continue

                analysis = await asyncio.get_event_loop().run_in_executor(
                    None, ta_service.analyze, symbol, timeframe, candles
                )

                confluence = analysis.get("confluence_score", 0.5)
                signal = analysis.get("signal", "wait")

                if signal != "wait" and confluence >= CONFLUENCE_THRESHOLD:
                    signal_record = {
                        "symbol": symbol,
                        "signal": signal,
                        "confluence_score": confluence,
                        "entry": analysis.get("entry"),
                        "stop_loss": analysis.get("stop_loss"),
                        "take_profit_1": analysis.get("take_profit_1"),
                        "take_profit_2": analysis.get("take_profit_2"),
                        "take_profit_3": analysis.get("take_profit_3"),
                        "trend": analysis.get("trend"),
                        "timeframe": timeframe,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "executed": False,
                        "mode": mode,
                    }

                    # Store signal
                    _signals.setdefault(user_id, []).append(signal_record)
                    if len(_signals[user_id]) > 100:
                        _signals[user_id] = _signals[user_id][-100:]

                    logger.info(
                        f"[BOT] Signal for {user_id}: {signal.upper()} {symbol} "
                        f"confluence={confluence:.2f}"
                    )

                    # In auto mode, execute via broker
                    if mode == "auto":
                        await _execute_signal(user_id, signal_record)

                    # In any mode, push via WebSocket (future: use Redis pub/sub)
                    await _broadcast_signal(user_id, signal_record)

            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error(f"Bot scan error for {symbol}: {e}")

        await asyncio.sleep(interval)


async def _execute_signal(user_id: str, signal: dict):
    """Execute a signal via connected broker in auto mode."""
    from routers.broker import _sessions
    svc = _sessions.get(user_id)
    if not svc:
        logger.warning(f"Auto execution skipped: no broker session for user {user_id}")
        return

    from services.capital_com import CapitalComService
    epic = CapitalComService.symbol_to_epic(signal["symbol"])
    if not epic:
        return

    try:
        direction = "BUY" if signal["signal"] == "buy" else "SELL"
        await svc.create_order(
            epic=epic,
            direction=direction,
            size=0.1,  # Default lot size
            stop_level=signal.get("stop_loss"),
            profit_level=signal.get("take_profit_1"),
        )
        signal["executed"] = True
        logger.info(f"Auto-executed {direction} {epic} for user {user_id}")
    except Exception as e:
        logger.error(f"Auto-execution failed for {user_id}: {e}")


async def _broadcast_signal(user_id: str, signal: dict):
    """Push signal to user's WebSocket connections."""
    from main import ws_connections
    ws = ws_connections.get(user_id)
    if ws:
        try:
            await ws.send_json({"type": "signal", "data": signal})
        except Exception:
            pass


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def get_bot_status(current_user: User = Depends(get_current_user)):
    """Get current bot status for the authenticated user."""
    user_id = str(current_user.id)
    state = _bot_state.get(user_id, {})
    return {
        "running": state.get("running", False),
        "mode": state.get("mode", "manual"),
        "symbols": state.get("symbols", []),
        "timeframe": state.get("timeframe", "H1"),
        "started_at": state.get("started_at"),
        "signal_count": len(_signals.get(user_id, [])),
        "confluence_threshold": CONFLUENCE_THRESHOLD,
    }


@router.post("/start")
async def start_bot(
    body: BotStartRequest,
    current_user: User = Depends(get_current_user),
):
    """Start the trading bot."""
    user_id = str(current_user.id)

    # Validate mode
    if body.mode not in ("auto", "semi_auto", "manual"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mode must be one of: auto, semi_auto, manual",
        )

    # Validate symbols
    invalid = [s for s in body.symbols if s not in SUPPORTED_SYMBOLS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported symbols: {invalid}",
        )

    # Check if already running
    existing = _bot_state.get(user_id, {})
    if existing.get("running"):
        task = existing.get("task")
        if task and not task.done():
            task.cancel()

    # Start new bot loop
    task = asyncio.create_task(
        _bot_loop(
            user_id,
            body.mode,
            body.symbols,
            body.timeframe,
            body.scan_interval_seconds,
        )
    )

    _bot_state[user_id] = {
        "running": True,
        "mode": body.mode,
        "symbols": body.symbols,
        "timeframe": body.timeframe,
        "scan_interval": body.scan_interval_seconds,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "task": task,
    }

    return {
        "status": "started",
        "mode": body.mode,
        "symbols": body.symbols,
        "timeframe": body.timeframe,
        "scan_interval_seconds": body.scan_interval_seconds,
        "message": f"Bot started in {body.mode} mode. Scanning {len(body.symbols)} symbols every {body.scan_interval_seconds}s.",
    }


@router.post("/stop")
async def stop_bot(current_user: User = Depends(get_current_user)):
    """Stop the trading bot."""
    user_id = str(current_user.id)
    state = _bot_state.get(user_id, {})

    if not state.get("running"):
        return {"status": "not_running", "message": "Bot was not running"}

    task = state.get("task")
    if task and not task.done():
        task.cancel()

    _bot_state[user_id] = {"running": False, "mode": state.get("mode"), "symbols": state.get("symbols", [])}

    return {"status": "stopped", "message": "Bot stopped successfully"}


@router.get("/signals")
async def get_signals(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """Get recent trading signals generated by the bot."""
    user_id = str(current_user.id)
    all_signals = _signals.get(user_id, [])
    # Return newest first
    recent = list(reversed(all_signals[-limit:]))
    return {
        "signals": recent,
        "count": len(recent),
        "total": len(all_signals),
    }


@router.get("/performance")
async def get_performance(
    current_user: User = Depends(get_current_user),
):
    """Get bot performance statistics from trade history."""
    from sqlalchemy import select, func
    from database import AsyncSessionLocal
    from models.trade import Trade
    import uuid

    user_id = current_user.id
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Trade).where(Trade.user_id == user_id)
        )
        trades = result.scalars().all()

    total = len(trades)
    closed = [t for t in trades if t.status == "closed"]
    open_trades = [t for t in trades if t.status == "open"]

    if not closed:
        return {
            "total_trades": total,
            "closed_trades": 0,
            "open_trades": len(open_trades),
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "profit_factor": 0.0,
            "avg_pnl": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }

    pnls = [t.pnl or 0.0 for t in closed]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    total_profit = sum(wins)
    total_loss = abs(sum(losses))
    profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

    return {
        "total_trades": total,
        "closed_trades": len(closed),
        "open_trades": len(open_trades),
        "win_rate": round(len(wins) / len(closed) * 100, 2) if closed else 0.0,
        "total_pnl": round(sum(pnls), 2),
        "profit_factor": round(profit_factor, 2),
        "avg_pnl": round(sum(pnls) / len(closed), 2),
        "best_trade": round(max(pnls), 2) if pnls else 0.0,
        "worst_trade": round(min(pnls), 2) if pnls else 0.0,
    }
