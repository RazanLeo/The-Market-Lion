"""News ingest Celery tasks."""
from __future__ import annotations
import asyncio
import json
import redis as redis_sync
from ...celery_app import celery
from ...core.config import settings
from ...core.logging import get_logger
from ..engines.news_pipeline import ingest_once

log = get_logger("news_tasks")


@celery.task(name="tasks.news.ingest_all")
def ingest_all() -> dict:
    saved = asyncio.run(ingest_once())
    if saved:
        try:
            r = redis_sync.from_url(settings.REDIS_URL, decode_responses=True)
            r.publish("news:global", json.dumps({"type": "news_batch", "saved": saved}))
        except Exception as e:
            log.warning("publish_fail", err=str(e))
    return {"ok": True, "saved": saved}


@celery.task(name="tasks.news.ingest_twitter")
def ingest_twitter() -> dict:
    # Twitter API v2 polling — placeholder until bearer token configured
    return {"ok": True, "saved": 0}


@celery.task(name="tasks.news.ingest_econ_calendar")
def ingest_econ_calendar() -> dict:
    """Pull live RSS calendars (ForexFactory + Investing.com + DailyFX) and persist."""
    from ...services.data_sources.fundamental import (
        fetch_forex_factory_calendar, fetch_investing_calendar_rss,
        fetch_dailyfx_news, affected_symbols,
    )
    from ...db.base import AsyncSessionLocal
    from ...db.models import EconomicEvent, NewsItem
    from sqlalchemy import insert
    from datetime import datetime, timezone
    import uuid

    async def _run():
        events = fetch_forex_factory_calendar()
        news = fetch_investing_calendar_rss() + fetch_dailyfx_news()
        saved_events = 0; saved_news = 0
        async with AsyncSessionLocal() as db:
            for ev in events:
                try:
                    await db.execute(insert(EconomicEvent).values(
                        id=uuid.uuid4(),
                        ts=ev["ts"], country=ev["country"], title=ev["title"],
                        impact_level=ev.get("impact", "low"),
                        previous_v=ev.get("previous"), forecast_v=ev.get("forecast"),
                        actual_v=ev.get("actual"),
                        symbols_affected=affected_symbols(ev["country"]),
                    ))
                    saved_events += 1
                except Exception as e:
                    log.debug("ev_skip", err=str(e))
            for n in news:
                try:
                    await db.execute(insert(NewsItem).values(
                        id=uuid.uuid4(),
                        ts=n["ts"], source=n.get("source", "rss"),
                        title=n["title"], url=n.get("url"),
                        category=n.get("category", "general"),
                        symbols=[],
                    ))
                    saved_news += 1
                except Exception as e:
                    log.debug("news_skip", err=str(e))
            await db.commit()
        return {"ok": True, "events_saved": saved_events, "news_saved": saved_news}

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run(_run())
        return loop.run_until_complete(_run())
    except RuntimeError:
        return asyncio.run(_run())
