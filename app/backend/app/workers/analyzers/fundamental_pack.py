"""Fundamental analyzers — News Sentiment + FOMC/NFP impact gate."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, desc
from ..engines.voting_engine import AnalyzerResult
from ...db.base import AsyncSessionLocal
from ...db.models import NewsItem, EconomicEvent


async def news_sentiment_analyzer(symbol: str) -> AnalyzerResult:
    """Aggregates last 6h of news for symbol → buy/sell/neutral based on weighted sentiment."""
    since = datetime.now(timezone.utc) - timedelta(hours=6)
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(NewsItem).where(NewsItem.ts >= since, NewsItem.symbols.any(symbol))
            .order_by(desc(NewsItem.ts)).limit(50)
        )).scalars().all()
    if not rows:
        return AnalyzerResult("news_sentiment", "neutral", 0, 1.0, {})
    weighted = 0.0
    total_impact = 0.0
    for n in rows:
        s = float(n.sentiment or 0)
        i = float(n.impact or 0)
        weighted += s * i
        total_impact += i
    if total_impact == 0:
        return AnalyzerResult("news_sentiment", "neutral", 0, 1.0, {"items": len(rows)})
    score = weighted / total_impact  # -100..+100
    confidence = min(85.0, abs(score) * 0.85)
    direction = "buy" if score > 5 else ("sell" if score < -5 else "neutral")
    return AnalyzerResult("news_sentiment", direction, confidence, 1.0,
                          {"items": len(rows), "score": round(score, 2), "total_impact": round(total_impact, 2)})


async def fomc_nfp_impact_analyzer(symbol: str) -> AnalyzerResult:
    """Returns neutral with HIGH weight if a high-impact event window is approaching → caller may halt trading.

    Treats this as a *gate* — if upcoming high-impact event, return signal=neutral with confidence 0
    AND payload.halt=True so the engine can pause auto-trading.
    """
    now = datetime.now(timezone.utc)
    soon = now + timedelta(minutes=30)
    async with AsyncSessionLocal() as db:
        ev = (await db.execute(
            select(EconomicEvent).where(
                EconomicEvent.ts >= now,
                EconomicEvent.ts <= soon,
                EconomicEvent.impact_level == "high",
            )
        )).scalars().all()
    if ev:
        return AnalyzerResult("fomc_nfp", "neutral", 0, 1.0,
                              {"halt": True, "events_in_30min": [e.title for e in ev]})
    return AnalyzerResult("fomc_nfp", "neutral", 0, 1.0, {"halt": False})
