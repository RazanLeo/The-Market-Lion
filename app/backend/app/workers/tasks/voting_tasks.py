"""Celery tasks: orchestrate analyzers → voting engine → confluence_scores → Redis pubsub.

Registry-driven: every analyzer in `analyzers/schools/`, `analyzers/indicators/`,
and `analyzers/tools/` is auto-discovered by `_registry.py` and called per
(symbol, tf). Persistence:
  - school + tool results        → school_signals table
  - indicator results            → indicator_signals table
  - aggregate confluence score   → confluence_scores table
"""
from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
import redis as redis_sync
from sqlalchemy import insert

from ...celery_app import celery
from ...core.config import settings
from ...core.logging import get_logger
from ...db.base import AsyncSessionLocal
from ...db.models import ConfluenceScoreRow, SchoolSignalRow, IndicatorSignalRow
from ...services.data_sources import get_ohlcv  # FREE Yahoo/Stooq, NOT Capital.com
from ..engines.voting_engine import compute_confluence, AnalyzerResult

# Legacy basics + flow + fundamental packs (real-time, low-latency primitives)
from ..analyzers.indicators_pack import (
    rsi_analyzer, ema_stack_analyzer, macd_analyzer, vwap_analyzer,
    bollinger_analyzer, atr_volatility_analyzer, adx_analyzer,
)
from ..analyzers.flow_pack import (
    volume_profile_analyzer, order_flow_basic_analyzer, bookmap_basic_analyzer,
)
from ..analyzers.fundamental_pack import news_sentiment_analyzer, fomc_nfp_impact_analyzer

# Full registry — 295 analyzers (schools=140, indicators=135, tools=20)
from ..analyzers._registry import SCHOOLS, INDICATORS, TOOLS

log = get_logger("voting_tasks")
WATCHLIST = ["XAUUSD", "USOIL", "EURUSD", "GBPUSD", "USDJPY"]
TIMEFRAMES = ["15M", "1H", "4H"]


def _safe_call(fn, df: pd.DataFrame) -> AnalyzerResult | None:
    """Run an analyzer; swallow per-analyzer failures so one bug doesn't kill the whole loop."""
    try:
        return fn(df)
    except Exception as e:  # pragma: no cover (defensive)
        log.warning("analyzer_failed", code=getattr(fn, "__module__", "?"), err=str(e))
        return None


def _persist_signals(rows_school: list, rows_indicator: list, ts: datetime, sym: str, tf: str):
    """Build SQL insert payloads — caller commits inside the same transaction."""
    school_payloads = []
    indicator_payloads = []
    for r in rows_school:
        if r is None:
            continue
        school_payloads.append({
            "ts": ts, "symbol": sym, "tf": tf, "school_code": r.code,
            "result": r.result,
            "confidence": Decimal(str(round(float(r.confidence or 0), 2))),
            "weight": Decimal(str(round(float(r.weight or 1.0), 2))),
            "payload": r.payload or {},
        })
    for r in rows_indicator:
        if r is None:
            continue
        indicator_payloads.append({
            "ts": ts, "symbol": sym, "tf": tf, "indicator_code": r.code,
            "result": r.result,
            "confidence": Decimal(str(round(float(r.confidence or 0), 2))),
            "weight": Decimal(str(round(float(r.weight or 1.0), 2))),
            "payload": r.payload or {},
        })
    return school_payloads, indicator_payloads


@celery.task(name="tasks.voting.recompute_all")
def recompute_all() -> dict[str, Any]:
    """Periodic: pull free OHLCV (Yahoo→Stooq) for each symbol×TF, run all 295 analyzers, persist confluence.

    Capital.com is intentionally NOT used here — it's only the user's execution
    broker, not the analysis data source. The market data is free + open.
    """
    async def _run() -> dict[str, Any]:
        log.info("recompute_start",
                 schools=len(SCHOOLS), indicators=len(INDICATORS), tools=len(TOOLS),
                 source="yahoo→stooq")

        results: list[dict[str, Any]] = []
        for sym in WATCHLIST:
            for tf in TIMEFRAMES:
                try:
                    df = get_ohlcv(sym, tf, 300)
                    if df.empty:
                        log.warning("recompute_no_data", sym=sym, tf=tf)
                        continue

                    # Basics — low-latency primitives kept as their own category
                    basics = [_safe_call(fn, df) for fn in (
                        rsi_analyzer, ema_stack_analyzer, macd_analyzer, vwap_analyzer,
                        bollinger_analyzer, atr_volatility_analyzer, adx_analyzer,
                    )]

                    # Schools — full registry (140 analyzers) + tools (20) merged into schools category
                    school_results = [_safe_call(fn, df) for fn in SCHOOLS.values()]
                    tool_results = [_safe_call(fn, df) for fn in TOOLS.values()]
                    schools_combined = [r for r in (school_results + tool_results) if r is not None]

                    # Indicators — full registry (135 analyzers)
                    indicator_results = [_safe_call(fn, df) for fn in INDICATORS.values()]
                    indicators_combined = [r for r in indicator_results if r is not None]

                    # Flow — legacy real-time primitives
                    flow = [_safe_call(fn, df) for fn in (
                        volume_profile_analyzer, order_flow_basic_analyzer, bookmap_basic_analyzer,
                    )]
                    flow = [r for r in flow if r is not None]

                    # Fundamental
                    try:
                        fund = [
                            await news_sentiment_analyzer(sym),
                            await fomc_nfp_impact_analyzer(sym),
                        ]
                        fund = [r for r in fund if r is not None]
                    except Exception:
                        fund = []

                    # Aggregate decision
                    decision = compute_confluence(
                        fundamental=fund,
                        basics=[r for r in basics if r is not None],
                        schools=schools_combined,
                        indicators=indicators_combined,
                        flow=flow,
                        threshold=settings.CONFLUENCE_THRESHOLD_DEFAULT,
                    )

                    ts = datetime.now(timezone.utc)
                    school_payloads, indicator_payloads = _persist_signals(
                        schools_combined, indicators_combined, ts, sym, tf
                    )

                    async with AsyncSessionLocal() as db:
                        # Confluence row
                        await db.execute(insert(ConfluenceScoreRow).values(
                            ts=ts, symbol=sym, tf=tf,
                            fundamental_pct=Decimal(str(decision["fundamental_pct"])),
                            basics_pct=Decimal(str(decision["basics_pct"])),
                            schools_pct=Decimal(str(decision["schools_pct"])),
                            indicators_pct=Decimal(str(decision["indicators_pct"])),
                            flow_pct=Decimal(str(decision["flow_pct"])),
                            total_pct=Decimal(str(decision["total_pct"])),
                            decision=decision["decision"],
                            payload=decision,
                        ))
                        # Per-analyzer rows (bulk insert chunked to be polite to PG)
                        if school_payloads:
                            for chunk_start in range(0, len(school_payloads), 100):
                                await db.execute(insert(SchoolSignalRow).values(
                                    school_payloads[chunk_start:chunk_start + 100]
                                ))
                        if indicator_payloads:
                            for chunk_start in range(0, len(indicator_payloads), 100):
                                await db.execute(insert(IndicatorSignalRow).values(
                                    indicator_payloads[chunk_start:chunk_start + 100]
                                ))
                        await db.commit()

                    # Publish
                    try:
                        r = redis_sync.from_url(settings.REDIS_URL, decode_responses=True)
                        r.publish(
                            f"analysis:{sym}:{tf}",
                            json.dumps({"type": "confluence", "symbol": sym, "tf": tf,
                                        **{k: decision[k] for k in ("total_pct", "decision", "direction")}})
                        )
                    except Exception as e:
                        log.warning("redis_publish_skip", err=str(e))

                    results.append({
                        "sym": sym, "tf": tf,
                        "decision": decision["decision"], "score": decision["total_pct"],
                        "n_schools": len(schools_combined),
                        "n_indicators": len(indicators_combined),
                    })
                    log.info("recompute_ok", sym=sym, tf=tf,
                             n_schools=len(schools_combined),
                             n_indicators=len(indicators_combined),
                             decision=decision["decision"])
                except Exception as e:
                    log.error("recompute_fail", sym=sym, tf=tf, err=str(e))

        return {"ok": True, "results": results,
                "registry": {"schools": len(SCHOOLS), "indicators": len(INDICATORS), "tools": len(TOOLS)}}

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run(_run())
        return loop.run_until_complete(_run())
    except RuntimeError:
        return asyncio.run(_run())


@celery.task(name="tasks.voting.run_rl_loop")
def run_rl_loop() -> dict[str, Any]:
    """Reinforcement learning — adjusts category weights after closed trades."""
    async def _run():
        from ..engines.learning_loop import run_loop_for_recent
        return await run_loop_for_recent()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run(_run())
        return loop.run_until_complete(_run())
    except RuntimeError:
        return asyncio.run(_run())
