"""Risk Manager Service — The Market Lion. Port 8013.
Handles entry/exit strategy, SL/TP management, position sizing,
killzone filtering, trailing stops, and trade session awareness.
"""
import asyncio
import json
import math
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, time
from typing import Any, Dict, List, Optional, Tuple

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from risk_manager import RiskManager, RiskConfig, PositionSize, TradeValidation

# ─── Models ───────────────────────────────────────────────────────────────────

class ValidateTradeRequest(BaseModel):
    capital: float = 10000.0
    entry: float
    sl: float
    side: str  # BUY | SELL
    atr: float
    pip_value: float = 0.0001
    swing_high: float
    swing_low: float
    open_trades_count: int = 0
    daily_loss_pct: float = 0.0
    drawdown_pct: float = 0.0
    consecutive_losses: int = 0
    news_shield_active: bool = False
    leverage: float = 100.0
    spread: float = 0.0
    swap_per_day: float = 0.0
    commission: float = 0.0


class PositionSizeRequest(BaseModel):
    capital: float = 10000.0
    entry: float
    sl: float
    pip_value: float = 0.0001
    leverage: float = 100.0
    risk_pct: float = 2.0


class EntryStrategyRequest(BaseModel):
    symbol: str
    side: str  # BUY | SELL
    confluence_score: float
    entry_price: float
    atr: float
    swing_high: float
    swing_low: float
    capital: float = 10000.0
    pip_value: float = 0.0001
    leverage: float = 100.0
    current_spread: float = 0.0
    timestamp_utc: Optional[str] = None  # ISO format


class TrailingStopRequest(BaseModel):
    side: str  # BUY | SELL
    entry: float
    current_sl: float
    current_price: float
    atr: float
    swing_high: Optional[float] = None
    swing_low: Optional[float] = None
    atr_multiplier: float = 1.5
    breakeven_triggered: bool = False
    pnl_r: float = 0.0  # current P&L in R multiples


class PyramidRequest(BaseModel):
    parent_entry: float
    parent_sl: float
    parent_side: str
    parent_pnl_pct: float
    parent_at_breakeven: bool
    new_confluence_score: float
    pyramid_count: int
    capital: float
    atr: float
    swing_high: float
    swing_low: float
    pip_value: float = 0.0001
    leverage: float = 100.0


class KillzoneRequest(BaseModel):
    timestamp_utc: str  # ISO format
    symbol: Optional[str] = None


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Risk Manager Service",
    description="Entry/Exit strategy, position sizing, SL/TP, killzones",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

risk = RiskManager()


# ─── Killzone helpers ─────────────────────────────────────────────────────────

KILLZONES = {
    "asian":    (time(0, 0),  time(6, 0)),
    "london":   (time(7, 0),  time(10, 30)),
    "ny":       (time(12, 0), time(15, 30)),
    "ny_close": (time(19, 30), time(20, 30)),
}

def _active_killzone(dt: datetime) -> Optional[str]:
    t = dt.time()
    for name, (start, end) in KILLZONES.items():
        if start <= t <= end:
            return name
    return None

def _is_high_volume_session(dt: datetime) -> bool:
    kz = _active_killzone(dt)
    return kz in ("london", "ny")

def _session_spread_limit(kz: Optional[str]) -> float:
    limits = {"asian": 0.0008, "london": 0.0003, "ny": 0.0003, "ny_close": 0.0005}
    return limits.get(kz, 0.0005)


# ─── Entry strategy helpers ───────────────────────────────────────────────────

def _ote_zone(swing_high: float, swing_low: float, side: str) -> Tuple[float, float]:
    """Optimal Trade Entry zone: 61.8%–79% Fibonacci retracement."""
    rng = swing_high - swing_low
    if side == "BUY":
        ote_high = swing_high - rng * 0.618
        ote_low  = swing_high - rng * 0.79
        return ote_low, ote_high
    else:
        ote_low  = swing_low + rng * 0.618
        ote_high = swing_low + rng * 0.79
        return ote_low, ote_high

def _entry_quality(entry: float, swing_high: float, swing_low: float, side: str) -> str:
    ote_low, ote_high = _ote_zone(swing_high, swing_low, side)
    if ote_low <= entry <= ote_high:
        return "OTE"
    rng = swing_high - swing_low
    if side == "BUY":
        if entry <= swing_high - rng * 0.5:
            return "DISCOUNT"
        return "PREMIUM"
    else:
        if entry >= swing_low + rng * 0.5:
            return "PREMIUM"
        return "DISCOUNT"

def _min_confluence_for_entry(killzone: Optional[str]) -> float:
    base = {"london": 65.0, "ny": 65.0, "asian": 70.0, "ny_close": 72.0}
    return base.get(killzone, 68.0)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "risk-manager-service", "status": "running", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    return ""


@app.post("/validate")
async def validate_trade(req: ValidateTradeRequest):
    """Full 5-layer trade validation."""
    result = risk.validate_trade(
        capital=req.capital,
        entry=req.entry,
        sl=req.sl,
        side=req.side,
        atr=req.atr,
        pip_value=req.pip_value,
        swing_high=req.swing_high,
        swing_low=req.swing_low,
        open_trades_count=req.open_trades_count,
        daily_loss_pct=req.daily_loss_pct,
        drawdown_pct=req.drawdown_pct,
        consecutive_losses=req.consecutive_losses,
        news_shield_active=req.news_shield_active,
        leverage=req.leverage,
        spread=req.spread,
        swap_per_day=req.swap_per_day,
        commission=req.commission,
    )
    return {
        "is_valid": result.is_valid,
        "rejection_reasons": result.rejection_reasons,
        "sl": result.sl_price,
        "tp1": result.tp1_price,
        "tp2": result.tp2_price,
        "tp3": result.tp3_price,
        "lot_size": result.lot_size,
        "risk_pct": result.risk_pct,
        "rr1": result.rr_1,
        "rr2": result.rr_2,
        "rr3": result.rr_3,
        "margin_required": result.margin_required,
        "commission_estimated": result.commission_estimated,
        "circuit_breaker_level": result.circuit_breaker_level,
    }


@app.post("/position-size")
async def position_size(req: PositionSizeRequest):
    """Calculate precise position size for given risk %."""
    cfg = RiskConfig(risk_per_trade_pct=req.risk_pct)
    rm = RiskManager(cfg)
    pos = rm.position_size(req.capital, req.entry, req.sl, req.pip_value, req.leverage)
    return {
        "lot_size": pos.lot_size,
        "risk_amount": pos.risk_amount,
        "risk_pct": pos.risk_pct,
        "sl_pips": pos.sl_pips,
        "margin_required": pos.margin_required,
        "leverage": pos.leverage,
    }


@app.post("/entry-strategy")
async def entry_strategy(req: EntryStrategyRequest):
    """Full entry strategy evaluation: killzone, OTE, spread, SL/TP plan."""
    now = datetime.now(timezone.utc)
    if req.timestamp_utc:
        try:
            now = datetime.fromisoformat(req.timestamp_utc)
        except Exception:
            pass

    kz = _active_killzone(now)
    high_vol = _is_high_volume_session(now)
    spread_limit = _session_spread_limit(kz)
    spread_ok = req.current_spread <= spread_limit

    min_conf = _min_confluence_for_entry(kz)
    conf_ok = req.confluence_score >= min_conf

    quality = _entry_quality(req.entry_price, req.swing_high, req.swing_low, req.side)
    ote_low, ote_high = _ote_zone(req.swing_high, req.swing_low, req.side)

    sl = risk.smart_stop_loss(req.entry_price, req.side, req.atr, req.swing_high, req.swing_low)
    tp1, tp2, tp3 = risk.calculate_take_profits(req.entry_price, sl, req.side)

    pos = risk.position_size(req.capital, req.entry_price, sl, req.pip_value, req.leverage)

    risk_dist = abs(req.entry_price - sl)
    rr1 = abs(tp1 - req.entry_price) / risk_dist if risk_dist else 1.0
    rr2 = abs(tp2 - req.entry_price) / risk_dist if risk_dist else 2.0
    rr3 = abs(tp3 - req.entry_price) / risk_dist if risk_dist else 3.0

    # TP allocation: 25% TP1, 50% TP2, 25% TP3
    lot = pos.lot_size
    lots_tp1 = round(lot * 0.25, 2)
    lots_tp2 = round(lot * 0.50, 2)
    lots_tp3 = round(lot * 0.25, 2)

    # Breakeven trigger: move SL to entry after TP1 hit
    breakeven_trigger_price = tp1

    warnings = []
    if not spread_ok:
        warnings.append(f"SPREAD_HIGH: {req.current_spread:.5f} > limit {spread_limit:.5f}")
    if not conf_ok:
        warnings.append(f"LOW_CONFLUENCE: {req.confluence_score:.1f} < {min_conf:.1f} required for {kz or 'no-killzone'}")
    if quality == "PREMIUM" and req.side == "BUY":
        warnings.append("BUYING_IN_PREMIUM_ZONE")
    if quality == "DISCOUNT" and req.side == "SELL":
        warnings.append("SELLING_IN_DISCOUNT_ZONE")
    if not kz:
        warnings.append("NOT_IN_KILLZONE — lower probability session")

    should_enter = conf_ok and spread_ok and len([w for w in warnings if "PREMIUM" in w or "DISCOUNT" in w]) == 0

    return {
        "should_enter": should_enter,
        "warnings": warnings,
        "killzone": kz,
        "high_volume_session": high_vol,
        "entry_quality": quality,
        "ote_zone": {"low": round(ote_low, 5), "high": round(ote_high, 5)},
        "sl": round(sl, 5),
        "tp1": round(tp1, 5),
        "tp2": round(tp2, 5),
        "tp3": round(tp3, 5),
        "rr1": round(rr1, 2),
        "rr2": round(rr2, 2),
        "rr3": round(rr3, 2),
        "lot_size": lot,
        "allocation": {"tp1": lots_tp1, "tp2": lots_tp2, "tp3": lots_tp3},
        "breakeven_trigger": round(breakeven_trigger_price, 5),
        "risk_amount": pos.risk_amount,
        "margin_required": pos.margin_required,
        "min_confluence_required": min_conf,
    }


@app.post("/trailing-stop")
async def trailing_stop(req: TrailingStopRequest):
    """Calculate updated trailing stop based on current market position."""
    atr_trail = req.atr * req.atr_multiplier

    if req.side == "BUY":
        # ATR trail
        atr_new_sl = req.current_price - atr_trail
        # Swing trail (last known swing low)
        swing_sl = (req.swing_low - req.atr * 0.5) if req.swing_low else None
        # Breakeven
        be_sl = req.entry if req.breakeven_triggered else None

        candidates = [c for c in [atr_new_sl, swing_sl, be_sl] if c is not None]
        # For BUY: new SL must be above current SL (tighter) and below current price
        valid = [c for c in candidates if req.current_sl < c < req.current_price]
        new_sl = max(valid) if valid else req.current_sl

        # Breakeven trigger at 1R
        r_dist = abs(req.entry - req.current_sl)
        be_trigger = req.entry + r_dist if r_dist else req.current_price
        trigger_be = req.current_price >= be_trigger and not req.breakeven_triggered

    else:
        atr_new_sl = req.current_price + atr_trail
        swing_sl = (req.swing_high + req.atr * 0.5) if req.swing_high else None
        be_sl = req.entry if req.breakeven_triggered else None

        candidates = [c for c in [atr_new_sl, swing_sl, be_sl] if c is not None]
        valid = [c for c in candidates if req.current_price < c < req.current_sl]
        new_sl = min(valid) if valid else req.current_sl

        r_dist = abs(req.entry - req.current_sl)
        be_trigger = req.entry - r_dist if r_dist else req.current_price
        trigger_be = req.current_price <= be_trigger and not req.breakeven_triggered

    moved = new_sl != req.current_sl
    pnl_r = req.pnl_r
    if req.current_sl and abs(req.entry - req.current_sl) > 0:
        pnl_r = abs(req.current_price - req.entry) / abs(req.entry - req.current_sl)
        if req.side == "SELL":
            pnl_r = pnl_r if req.current_price < req.entry else -pnl_r
        else:
            pnl_r = pnl_r if req.current_price > req.entry else -pnl_r

    return {
        "new_sl": round(new_sl, 5),
        "sl_moved": moved,
        "trigger_breakeven": trigger_be,
        "current_pnl_r": round(pnl_r, 2),
        "atr_trail_sl": round(atr_new_sl, 5),
        "method": "atr_trail" if moved and abs(new_sl - atr_new_sl) < 0.00001 else "swing_trail",
    }


@app.post("/pyramid")
async def pyramid_check(req: PyramidRequest):
    """Evaluate whether to add to a winning position (pyramiding)."""
    allowed, reasons = risk.check_pyramiding_allowed(
        parent_pnl_pct=req.parent_pnl_pct,
        parent_at_breakeven=req.parent_at_breakeven,
        new_confluence_score=req.new_confluence_score,
        pyramid_count=req.pyramid_count,
        new_lot_fraction=0.5,
    )

    if not allowed:
        return {"allowed": False, "reasons": reasons}

    # New SL at parent entry (breakeven) — pyramid SL is always tighter
    new_sl = req.parent_entry
    new_entry = req.parent_entry  # would be refined by caller

    half_risk_cfg = RiskConfig(risk_per_trade_pct=1.0)  # half normal risk for pyramids
    rm2 = RiskManager(half_risk_cfg)
    sl = rm2.smart_stop_loss(new_entry, req.parent_side, req.atr, req.swing_high, req.swing_low)
    # For pyramid, SL must be at or beyond parent entry
    if req.parent_side == "BUY":
        sl = max(sl, req.parent_entry)
    else:
        sl = min(sl, req.parent_entry)

    tp1, tp2, tp3 = rm2.calculate_take_profits(new_entry, sl, req.parent_side)
    pos = rm2.position_size(req.capital, new_entry, sl, req.pip_value, req.leverage)

    return {
        "allowed": True,
        "reasons": [],
        "pyramid_sl": round(sl, 5),
        "tp1": round(tp1, 5),
        "tp2": round(tp2, 5),
        "tp3": round(tp3, 5),
        "lot_size": pos.lot_size,
        "risk_pct": 1.0,
        "note": "50% of normal position size, SL at or beyond parent entry",
    }


@app.post("/killzone")
async def killzone_check(req: KillzoneRequest):
    """Check which trading session/killzone is currently active."""
    try:
        dt = datetime.fromisoformat(req.timestamp_utc)
    except Exception:
        dt = datetime.now(timezone.utc)

    kz = _active_killzone(dt)
    high_vol = _is_high_volume_session(dt)
    spread_limit = _session_spread_limit(kz)

    all_kz = {}
    for name, (start, end) in KILLZONES.items():
        all_kz[name] = {"start": start.isoformat(), "end": end.isoformat()}

    return {
        "active_killzone": kz,
        "high_volume_session": high_vol,
        "spread_limit": spread_limit,
        "utc_time": dt.time().isoformat(),
        "all_killzones": all_kz,
        "recommendation": (
            "TRADE" if kz in ("london", "ny") else
            "CAUTION" if kz == "asian" else
            "AVOID"
        ),
    }


@app.post("/circuit-breaker")
async def circuit_breaker(
    daily_loss_pct: float = 0.0,
    weekly_loss_pct: float = 0.0,
    monthly_loss_pct: float = 0.0,
    drawdown_pct: float = 0.0,
    consecutive_losses: int = 0,
):
    """Evaluate circuit breaker level and trading permission."""
    level, reasons = risk.check_circuit_breaker(
        daily_loss_pct, weekly_loss_pct, monthly_loss_pct, drawdown_pct, consecutive_losses
    )
    actions = {
        0: "TRADE_NORMAL",
        1: "PAUSE_2H",
        2: "STOP_TODAY",
        3: "REDUCE_SIZE_50PCT",
        4: "STOP_TRADING",
        5: "PERMANENT_STOP",
    }
    return {
        "circuit_breaker_level": level,
        "action": actions.get(level, "UNKNOWN"),
        "reasons": reasons,
        "can_trade": level < 2,
    }


@app.get("/session-info")
async def session_info():
    """Current session information."""
    now = datetime.now(timezone.utc)
    kz = _active_killzone(now)
    return {
        "utc_now": now.isoformat(),
        "active_killzone": kz,
        "high_volume": _is_high_volume_session(now),
        "spread_limit": _session_spread_limit(kz),
        "sessions": {
            name: {
                "start_utc": f"{s.isoformat()}",
                "end_utc": f"{e.isoformat()}",
                "active": _active_killzone(now) == name,
            }
            for name, (s, e) in KILLZONES.items()
        },
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8013, reload=True, log_level="info")
