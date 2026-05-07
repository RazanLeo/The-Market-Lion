"""News + Sentiment pipeline (FinBERT + GPT summarizer).

For first launch: keyword-based lightweight sentiment until FinBERT model is downloaded;
real model loads at first call inside worker process.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select

from ...core.config import settings
from ...core.logging import get_logger
from ...db.base import AsyncSessionLocal
from ...db.models import NewsItem, EconomicEvent

log = get_logger("news_pipeline")

ASSET_KEYWORDS = {
    "XAUUSD": ["gold", "xau", "ذهب", "fed gold", "comex gold", "lbma"],
    "USOIL":  ["oil", "crude", "wti", "نفط", "opec", "ضbara", "barrel"],
    "DXY":    ["dxy", "dollar index", "us dollar", "الدولار"],
    "EURUSD": ["euro", "eurusd", "ecb", "lagarde"],
    "GBPUSD": ["gbp", "pound", "boe", "uk economy"],
    "USDJPY": ["jpy", "yen", "boj", "japan"],
}

POSITIVE_TOKENS = {"surge", "rally", "rises", "bullish", "beat", "strong", "هبوط الدولار", "ارتفاع الذهب"}
NEGATIVE_TOKENS = {"plunge", "falls", "bearish", "miss", "weak", "ارتفاع الدولار", "هبوط الذهب", "downgrade"}


def map_symbols(text: str) -> list[str]:
    t = (text or "").lower()
    out: list[str] = []
    for sym, kws in ASSET_KEYWORDS.items():
        if any(k.lower() in t for k in kws):
            out.append(sym)
    return out


def naive_sentiment(text: str) -> tuple[float, float]:
    t = (text or "").lower()
    pos = sum(1 for k in POSITIVE_TOKENS if k in t)
    neg = sum(1 for k in NEGATIVE_TOKENS if k in t)
    if pos == 0 and neg == 0: return 0.0, 5.0
    score = (pos - neg) / max(pos + neg, 1)
    impact = min((pos + neg) * 15, 100)
    return round(score * 100, 2), round(impact, 2)


async def fetch_newsapi(query: str, api_key: str | None) -> list[dict[str, Any]]:
    if not api_key: return []
    async with httpx.AsyncClient(timeout=15) as cx:
        r = await cx.get("https://newsapi.org/v2/everything",
                         params={"q": query, "language": "en", "sortBy": "publishedAt", "pageSize": 50},
                         headers={"X-Api-Key": api_key})
        if r.status_code != 200:
            log.warning("newsapi_err", status=r.status_code)
            return []
        return r.json().get("articles", [])


async def ingest_once() -> int:
    """Single ingest cycle. Pulls from NewsAPI, dedupes by URL, scores, stores."""
    if not settings.NEWSAPI_KEY:
        return 0
    queries = ["gold price", "crude oil", "us dollar index", "federal reserve", "ECB", "OPEC"]
    saved = 0
    async with AsyncSessionLocal() as db:
        for q in queries:
            articles = await fetch_newsapi(q, settings.NEWSAPI_KEY)
            for a in articles:
                url = a.get("url")
                if not url: continue
                exists = (await db.execute(select(NewsItem).where(NewsItem.url == url))).scalar_one_or_none()
                if exists: continue
                title = a.get("title") or ""
                body = a.get("description") or ""
                full = f"{title}\n{body}"
                syms = map_symbols(full)
                sent, impact = naive_sentiment(full)
                ts_str = a.get("publishedAt") or datetime.now(timezone.utc).isoformat()
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except Exception:
                    ts = datetime.now(timezone.utc)
                row = NewsItem(
                    source=a.get("source", {}).get("name") or "NewsAPI",
                    url=url, ts=ts,
                    title=title, body=body, symbols=syms,
                    sentiment=sent, impact=impact, category="news",
                    raw=a,
                )
                db.add(row); saved += 1
        await db.commit()
    return saved
