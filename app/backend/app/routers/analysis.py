"""Analysis endpoints — runs the full 295-analyzer registry on LIVE Yahoo Finance data.

Every endpoint:
  1. Fetches fresh OHLCV from Yahoo Finance (free, public, no API key)
  2. Runs the relevant analyzers from the auto-discovered registry
  3. Returns each analyzer's result + confidence + payload
  4. Caches in Redis for 30s to keep latency low

This is what powers the 8 dashboard tables. The user sees actual analyzer
verdicts on real market data — not synthetic.
"""
from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone, timedelta
from typing import Annotated

import redis as redis_sync
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.logging import get_logger
from ..deps import current_user
from ..db.base import get_db
from ..db.models import User, NewsItem, EconomicEvent, ConfluenceScoreRow
from ..services.data_sources import get_ohlcv as yahoo_ohlcv  # alias preserves call sites

router = APIRouter()
log = get_logger("analysis")

CACHE_TTL = 30  # 30s cache so dashboard polling doesn't hammer Yahoo


def _redis():
    try:
        return redis_sync.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


def _cache_get(key: str):
    r = _redis()
    if r is None: return None
    try:
        v = r.get(key)
        return json.loads(v) if v else None
    except Exception:
        return None


def _cache_set(key: str, value, ttl: int = CACHE_TTL):
    r = _redis()
    if r is None: return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def _safe(fn, df):
    try:
        warnings.filterwarnings("ignore")
        return fn(df)
    except Exception as e:  # pragma: no cover
        log.debug("analyzer_skip", err=str(e))
        return None


@router.get("/fundamental")
async def fundamental(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    symbol: str = Query(..., description="e.g. XAUUSD"),
    tf: str = Query("15M"),
):
    """Fundamental table — news + economic events affecting the symbol."""
    since = datetime.now(timezone.utc) - timedelta(days=2)
    try:
        news = (await db.execute(
            select(NewsItem).where(NewsItem.ts >= since, NewsItem.symbols.any(symbol))
            .order_by(desc(NewsItem.ts)).limit(50)
        )).scalars().all()
        events = (await db.execute(
            select(EconomicEvent).where(EconomicEvent.ts >= since, EconomicEvent.symbols_affected.any(symbol))
            .order_by(desc(EconomicEvent.ts)).limit(30)
        )).scalars().all()
    except Exception as e:
        log.warning("fundamental_db_skip", err=str(e))
        news, events = [], []

    return {
        "ok": True, "symbol": symbol, "tf": tf,
        "news": [{
            "id": str(n.id), "ts": n.ts.isoformat(), "source": n.source,
            "title": n.title, "sentiment": float(n.sentiment or 0),
            "impact": float(n.impact or 0), "category": n.category,
        } for n in news],
        "events": [{
            "id": str(e.id), "ts": e.ts.isoformat(), "country": e.country,
            "title": e.title, "previous": float(e.previous_v) if e.previous_v else None,
            "forecast": float(e.forecast_v) if e.forecast_v else None,
            "actual": float(e.actual_v) if e.actual_v else None,
            "impact": e.impact_level,
        } for e in events],
    }


@router.get("/basics")
async def basics(
    user: Annotated[User, Depends(current_user)],
    symbol: str, tf: str = "15M",
):
    """Table 3 — basic technical primitives (RSI, MACD, EMA stack, Bollinger, ATR, ADX, VWAP)."""
    cache_key = f"analysis:basics:{symbol}:{tf}"
    cached = _cache_get(cache_key)
    if cached: return cached

    df = yahoo_ohlcv(symbol, tf, 300)
    if df.empty:
        return {"ok": False, "error": "no_data", "symbol": symbol, "tf": tf, "basics": []}

    from ..workers.analyzers.indicators_pack import (
        rsi_analyzer, ema_stack_analyzer, macd_analyzer, vwap_analyzer,
        bollinger_analyzer, atr_volatility_analyzer, adx_analyzer,
    )
    fns = [rsi_analyzer, ema_stack_analyzer, macd_analyzer, vwap_analyzer,
           bollinger_analyzer, atr_volatility_analyzer, adx_analyzer]
    rows = []
    for fn in fns:
        r = _safe(fn, df)
        if r is None: continue
        rows.append({"code": r.code, "result": r.result,
                     "confidence": float(r.confidence or 0),
                     "weight": float(r.weight or 1.0),
                     "payload": r.payload or {}})
    out = {"ok": True, "symbol": symbol, "tf": tf, "basics": rows,
           "ts": datetime.now(timezone.utc).isoformat()}
    _cache_set(cache_key, out)
    return out


@router.get("/schools")
async def schools(
    user: Annotated[User, Depends(current_user)],
    symbol: str, tf: str = "15M",
):
    """Table 4 — every school analyzer (140 schools + 20 tools = 160 verdicts)."""
    cache_key = f"analysis:schools:{symbol}:{tf}"
    cached = _cache_get(cache_key)
    if cached: return cached

    df = yahoo_ohlcv(symbol, tf, 300)
    if df.empty:
        return {"ok": False, "error": "no_data", "symbol": symbol, "tf": tf, "schools": []}

    from ..workers.analyzers._registry import SCHOOLS, TOOLS
    rows = []
    for code, fn in {**SCHOOLS, **TOOLS}.items():
        r = _safe(fn, df)
        if r is None: continue
        rows.append({"code": r.code, "result": r.result,
                     "confidence": float(r.confidence or 0),
                     "weight": float(r.weight or 1.0),
                     "payload": r.payload or {}})
    rows.sort(key=lambda x: -x["confidence"])
    out = {"ok": True, "symbol": symbol, "tf": tf, "schools": rows,
           "count": len(rows),
           "ts": datetime.now(timezone.utc).isoformat()}
    _cache_set(cache_key, out)
    return out


@router.get("/indicators")
async def indicators(
    user: Annotated[User, Depends(current_user)],
    symbol: str, tf: str = "15M",
):
    """Table 5 — every indicator analyzer (135)."""
    cache_key = f"analysis:indicators:{symbol}:{tf}"
    cached = _cache_get(cache_key)
    if cached: return cached

    df = yahoo_ohlcv(symbol, tf, 300)
    if df.empty:
        return {"ok": False, "error": "no_data", "symbol": symbol, "tf": tf, "indicators": []}

    from ..workers.analyzers._registry import INDICATORS
    rows = []
    for code, fn in INDICATORS.items():
        r = _safe(fn, df)
        if r is None: continue
        rows.append({"code": r.code, "result": r.result,
                     "confidence": float(r.confidence or 0),
                     "weight": float(r.weight or 1.0),
                     "payload": r.payload or {}})
    rows.sort(key=lambda x: -x["confidence"])
    out = {"ok": True, "symbol": symbol, "tf": tf, "indicators": rows,
           "count": len(rows),
           "ts": datetime.now(timezone.utc).isoformat()}
    _cache_set(cache_key, out)
    return out


@router.get("/flow")
async def flow(
    user: Annotated[User, Depends(current_user)],
    symbol: str, tf: str = "15M",
):
    """Table 6 — order flow + Bookmap proxy events (computed from OHLCV)."""
    cache_key = f"analysis:flow:{symbol}:{tf}"
    cached = _cache_get(cache_key)
    if cached: return cached

    df = yahoo_ohlcv(symbol, tf, 300)
    if df.empty:
        return {"ok": False, "error": "no_data", "symbol": symbol, "tf": tf}

    from ..workers.analyzers.flow_pack import (
        volume_profile_analyzer, order_flow_basic_analyzer, bookmap_basic_analyzer,
    )
    items = []
    for fn in [volume_profile_analyzer, order_flow_basic_analyzer, bookmap_basic_analyzer]:
        r = _safe(fn, df)
        if r is None: continue
        items.append({"code": r.code, "result": r.result,
                      "confidence": float(r.confidence or 0),
                      "payload": r.payload or {}})

    # Real order-flow data: Binance L2 for crypto, OHLCV reconstruction for FX/commodities
    from ..services.data_sources.order_flow import get_order_flow
    flow_data = get_order_flow(symbol, df)
    direction = "buy" if flow_data.get("imbalance_pct", 0) > 5 else "sell" if flow_data.get("imbalance_pct", 0) < -5 else "neutral"

    out = {"ok": True, "symbol": symbol, "tf": tf,
           "items": items,
           "buy_volume": flow_data.get("buy_volume", 0),
           "sell_volume": flow_data.get("sell_volume", 0),
           "imbalance_pct": flow_data.get("imbalance_pct", 0),
           "absorption_bars": flow_data.get("absorption_bars", 0),
           "sweeps_up": flow_data.get("sweeps_up", 0),
           "sweeps_dn": flow_data.get("sweeps_dn", 0),
           "depth": flow_data.get("depth"),  # only for crypto
           "type": flow_data.get("type", "ohlcv_proxy"),
           "direction": direction,
           "ts": datetime.now(timezone.utc).isoformat()}
    _cache_set(cache_key, out)
    return out


@router.get("/confluence")
async def confluence(
    user: Annotated[User, Depends(current_user)],
    symbol: str, tf: str = "15M",
):
    """Table 8 — final decision: aggregate confluence score over all categories.

    Computes live (no DB dependency) so it works the moment the user logs in.
    """
    cache_key = f"analysis:confluence:{symbol}:{tf}"
    cached = _cache_get(cache_key)
    if cached: return cached

    df = yahoo_ohlcv(symbol, tf, 300)
    if df.empty:
        return {"ok": False, "error": "no_data", "symbol": symbol, "tf": tf,
                "decision": "wait", "total_pct": 0}

    from ..workers.analyzers._registry import SCHOOLS, INDICATORS, TOOLS
    from ..workers.analyzers.indicators_pack import (
        rsi_analyzer, ema_stack_analyzer, macd_analyzer, vwap_analyzer,
        bollinger_analyzer, atr_volatility_analyzer, adx_analyzer,
    )
    from ..workers.analyzers.flow_pack import (
        volume_profile_analyzer, order_flow_basic_analyzer, bookmap_basic_analyzer,
    )
    from ..workers.engines.voting_engine import compute_confluence

    basics_results = [_safe(fn, df) for fn in (
        rsi_analyzer, ema_stack_analyzer, macd_analyzer, vwap_analyzer,
        bollinger_analyzer, atr_volatility_analyzer, adx_analyzer)]
    schools_results = [_safe(fn, df) for fn in SCHOOLS.values()]
    tools_results = [_safe(fn, df) for fn in TOOLS.values()]
    indicators_results = [_safe(fn, df) for fn in INDICATORS.values()]
    flow_results = [_safe(fn, df) for fn in (
        volume_profile_analyzer, order_flow_basic_analyzer, bookmap_basic_analyzer)]

    decision = compute_confluence(
        fundamental=[],
        basics=[r for r in basics_results if r is not None],
        schools=[r for r in (schools_results + tools_results) if r is not None],
        indicators=[r for r in indicators_results if r is not None],
        flow=[r for r in flow_results if r is not None],
        threshold=settings.CONFLUENCE_THRESHOLD_DEFAULT,
    )

    last_close = float(df["c"].iloc[-1])
    out = {"ok": True, "symbol": symbol, "tf": tf,
           "fundamental_pct": float(decision["fundamental_pct"]),
           "basics_pct": float(decision["basics_pct"]),
           "schools_pct": float(decision["schools_pct"]),
           "indicators_pct": float(decision["indicators_pct"]),
           "flow_pct": float(decision["flow_pct"]),
           "total_pct": float(decision["total_pct"]),
           "decision": decision["decision"],
           "direction": decision.get("direction"),
           "current_price": last_close,
           "ts": datetime.now(timezone.utc).isoformat()}
    _cache_set(cache_key, out, ttl=15)  # decision cached only 15s
    return out


@router.get("/trade-plan")
async def trade_plan(
    user: Annotated[User, Depends(current_user)],
    symbol: str, tf: str = "15M",
    balance: float = 10000.0, risk_pct: float = 1.0,
):
    """Table 7 — concrete trade plan (entry / SL / TP1-3 / lot size / R:R)."""
    cache_key = f"analysis:plan:{symbol}:{tf}:{balance}:{risk_pct}"
    cached = _cache_get(cache_key)
    if cached: return cached

    df = yahoo_ohlcv(symbol, tf, 300)
    if df.empty:
        return {"ok": False, "error": "no_data"}

    # Get the live decision first
    conf_resp = await confluence(user, symbol, tf)
    if not conf_resp.get("ok"):
        return conf_resp

    direction = conf_resp.get("direction") or "wait"
    last_c = float(df["c"].iloc[-1])

    # ATR-based SL (1.5×ATR), TP at 1R / 2R / 3R
    import pandas as pd
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1] or 0)

    if direction == "buy":
        entry = last_c
        sl = entry - 1.5 * atr
        risk = entry - sl
        tp1 = entry + risk * 1.0
        tp2 = entry + risk * 2.0
        tp3 = entry + risk * 3.0
    elif direction == "sell":
        entry = last_c
        sl = entry + 1.5 * atr
        risk = sl - entry
        tp1 = entry - risk * 1.0
        tp2 = entry - risk * 2.0
        tp3 = entry - risk * 3.0
    else:
        out = {"ok": True, "symbol": symbol, "tf": tf, "direction": "wait",
               "reason": "Confluence below threshold",
               "current_price": last_c, "atr": round(atr, 5),
               "ts": datetime.now(timezone.utc).isoformat()}
        _cache_set(cache_key, out)
        return out

    # Position sizing
    risk_dollars = balance * (risk_pct / 100)
    pip_value = 1.0  # simplified — real pip-value depends on the pair
    lot_size = round(risk_dollars / max(abs(risk), 1e-9) / 100, 2)

    out = {"ok": True, "symbol": symbol, "tf": tf, "direction": direction,
           "current_price": round(last_c, 5), "atr": round(atr, 5),
           "entry": round(entry, 5), "sl": round(sl, 5),
           "tp1": round(tp1, 5), "tp2": round(tp2, 5), "tp3": round(tp3, 5),
           "risk_pct": risk_pct, "risk_amount": round(risk_dollars, 2),
           "suggested_lot": lot_size,
           "rr_tp1": "1:1", "rr_tp2": "1:2", "rr_tp3": "1:3",
           "confluence_score": conf_resp.get("total_pct"),
           "ts": datetime.now(timezone.utc).isoformat()}
    _cache_set(cache_key, out)
    return out


@router.get("/drawings")
async def drawings(
    user: Annotated[User, Depends(current_user)],
    symbol: str, tf: str = "15M",
):
    """Live drawings overlay from all 20 chart tools (lines/rects/markers)."""
    df = yahoo_ohlcv(symbol, tf, 300)
    if df.empty:
        return {"ok": False, "error": "no_data", "drawings": []}

    from ..workers.analyzers._registry import TOOLS
    drawings_out: list[dict] = []
    tools_summary: list[dict] = []
    for code, fn in TOOLS.items():
        r = _safe(fn, df)
        if r is None: continue
        if isinstance(r.payload, dict) and "drawings" in r.payload:
            for d in r.payload["drawings"]:
                drawings_out.append({**d, "tool": r.code})
        tools_summary.append({"code": r.code, "result": r.result,
                              "confidence": float(r.confidence or 0)})
    return {"ok": True, "symbol": symbol, "tf": tf,
            "drawings": drawings_out, "tools": tools_summary,
            "total_drawings": len(drawings_out),
            "ts": datetime.now(timezone.utc).isoformat()}
