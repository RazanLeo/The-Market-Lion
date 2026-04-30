"""News Ingestion Service — The Market Lion.
Pulls news from RSS feeds, ForexFactory economic calendar, and free APIs.
Runs NLP sentiment scoring, stores to MongoDB, publishes signals to Kafka.
"""
import asyncio
import logging
import os
import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
from fastapi import FastAPI, BackgroundTasks
import motor.motor_asyncio
from aiokafka import AIOKafkaProducer

logger = logging.getLogger("news-ingestion")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="News Ingestion Service", version="1.0.0")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
KAFKA_URL = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


class Impact(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class Sentiment(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class NewsArticle:
    id: str
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime
    assets: List[str]
    currencies: List[str]
    sentiment: Sentiment
    sentiment_score: float
    impact: Impact
    keywords: List[str]
    category: str


@dataclass
class EconomicEvent:
    id: str
    title: str
    currency: str
    country: str
    impact: Impact
    actual: Optional[float]
    forecast: Optional[float]
    previous: Optional[float]
    event_time: datetime
    surprise: Optional[float]
    surprise_pct: Optional[float]
    affected_assets: List[str]
    sentiment: Sentiment
    sentiment_score: float


ASSET_KEYWORDS: Dict[str, List[str]] = {
    "XAUUSD": ["gold", "xau", "precious metals", "bullion"],
    "XAGUSD": ["silver", "xag"],
    "USOIL":  ["oil", "crude", "wti", "opec", "energy", "petroleum"],
    "XBRUSD": ["brent", "crude oil"],
    "EURUSD": ["euro", "eur", "ecb", "eurozone", "lagarde"],
    "GBPUSD": ["pound", "gbp", "sterling", "boe", "bank of england"],
    "USDJPY": ["yen", "jpy", "boj", "bank of japan"],
    "AUDUSD": ["aussie", "aud", "rba", "australia"],
    "USDCHF": ["franc", "chf", "snb", "switzerland"],
    "USDCAD": ["cad", "loonie", "boc", "canada"],
    "BTCUSD": ["bitcoin", "btc", "crypto", "cryptocurrency"],
    "ETHUSD": ["ethereum", "eth", "ether"],
    "SOLUSD": ["solana", "sol"],
}

CURRENCY_COUNTRIES: Dict[str, str] = {
    "USD": "United States", "EUR": "Euro Zone", "GBP": "United Kingdom",
    "JPY": "Japan", "CHF": "Switzerland", "CAD": "Canada", "AUD": "Australia",
    "NZD": "New Zealand", "CNY": "China", "XAU": "Gold",
}

BULLISH_WORDS = [
    "rise", "rising", "surge", "rally", "gain", "bull", "bullish", "beat", "strong",
    "positive", "growth", "increase", "higher", "upside", "recovery", "hawkish",
    "hike", "outperform", "record high", "better than expected", "demand", "boost",
]

BEARISH_WORDS = [
    "fall", "falling", "drop", "decline", "bear", "bearish", "miss", "weak",
    "negative", "recession", "decrease", "lower", "downside", "dovish", "cut",
    "underperform", "record low", "worse than expected", "fear", "sell-off", "crash",
]

HIGH_IMPACT_KEYWORDS = [
    "fed", "federal reserve", "fomc", "interest rate", "cpi", "inflation",
    "gdp", "nonfarm", "nfp", "payroll", "ecb", "boe", "rate decision", "war",
    "geopolitical", "sanction", "crisis", "bank of japan", "bank of england",
]

RSS_FEEDS = [
    {"url": "https://www.forexlive.com/feed/news", "source": "ForexLive"},
    {"url": "https://www.fxstreet.com/rss/news", "source": "FXStreet"},
    {"url": "https://www.kitco.com/rss/kitco-news.xml", "source": "Kitco"},
    {"url": "https://cryptonews.com/news/feed/", "source": "CryptoNews"},
    {"url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines", "source": "MarketWatch"},
    {"url": "https://feeds.reuters.com/reuters/businessNews", "source": "Reuters"},
]

FOREX_FACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"


def keyword_sentiment(text: str) -> Tuple[Sentiment, float]:
    text_lower = text.lower()
    bull_count = sum(1 for w in BULLISH_WORDS if w in text_lower)
    bear_count = sum(1 for w in BEARISH_WORDS if w in text_lower)
    total = bull_count + bear_count
    if total == 0:
        return Sentiment.NEUTRAL, 0.0
    score = max(-1.0, min(1.0, (bull_count - bear_count) / total))
    if score > 0.1:
        return Sentiment.BULLISH, score
    elif score < -0.1:
        return Sentiment.BEARISH, score
    return Sentiment.NEUTRAL, score


def detect_assets(text: str) -> Tuple[List[str], List[str]]:
    text_lower = text.lower()
    assets, currencies = [], set()
    for asset, keywords in ASSET_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            assets.append(asset)
            currencies.add(asset[:3])
    for currency in CURRENCY_COUNTRIES:
        if currency.lower() in text_lower:
            currencies.add(currency)
    return assets, list(currencies)


def detect_impact(text: str, currencies: List[str]) -> Impact:
    text_lower = text.lower()
    if any(kw in text_lower for kw in HIGH_IMPACT_KEYWORDS):
        return Impact.HIGH
    if len(currencies) > 1:
        return Impact.MEDIUM
    return Impact.LOW


def extract_keywords(text: str) -> List[str]:
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    stop = {'that', 'this', 'with', 'from', 'they', 'have', 'been', 'will', 'said', 'says', 'also', 'more'}
    freq = {}
    for w in words:
        if w not in stop:
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:10]]


def detect_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["fed", "ecb", "boe", "central bank", "rate", "fomc"]):
        return "central_bank"
    if any(k in t for k in ["cpi", "gdp", "nfp", "payroll", "inflation", "retail"]):
        return "macro"
    if any(k in t for k in ["war", "conflict", "sanction", "geopolit"]):
        return "geopolitical"
    if any(k in t for k in ["bitcoin", "crypto", "ethereum"]):
        return "crypto"
    return "general"


def make_id(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def map_event_to_assets(currency: str) -> List[str]:
    mapping = {
        "USD": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF", "USDCAD", "XAUUSD", "USOIL", "BTCUSD"],
        "EUR": ["EURUSD", "EURGBP", "EURJPY"],
        "GBP": ["GBPUSD", "EURGBP", "GBPJPY"],
        "JPY": ["USDJPY", "EURJPY", "GBPJPY"],
        "AUD": ["AUDUSD"], "CAD": ["USDCAD"], "CHF": ["USDCHF"], "NZD": ["NZDUSD"],
    }
    return mapping.get(currency.upper(), [])


def score_economic_event(event: dict) -> Tuple[Sentiment, float]:
    def parse_val(s):
        if not s:
            return None
        try:
            return float(str(s).replace("%", "").replace("K", "000").replace("M", "000000").strip())
        except ValueError:
            return None

    actual = parse_val(event.get("actual"))
    forecast = parse_val(event.get("forecast"))
    previous = parse_val(event.get("previous"))
    if actual is None:
        return Sentiment.NEUTRAL, 0.0

    title_lower = event.get("title", "").lower()
    bearish_titles = ["unemployment", "jobless", "claims", "deficit", "inflation"]
    higher_is_better = not any(kw in title_lower for kw in bearish_titles)
    ref = forecast if forecast is not None else previous
    if ref is None:
        return Sentiment.NEUTRAL, 0.0

    surprise_pct = (actual - ref) / abs(ref) * 100 if ref != 0 else 0
    normalized = min(1.0, abs(surprise_pct) / 10)
    score = normalized if (surprise_pct > 0) == higher_is_better else -normalized
    if score > 0.15:
        return Sentiment.BULLISH, score
    elif score < -0.15:
        return Sentiment.BEARISH, score
    return Sentiment.NEUTRAL, score


async def parse_rss_feed(session: aiohttp.ClientSession, feed: dict) -> List[NewsArticle]:
    articles = []
    try:
        async with session.get(feed["url"], timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return articles
            text = await resp.text()
        items = re.findall(r'<item>(.*?)</item>', text, re.DOTALL)
        for item in items[:20]:
            title_m = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL)
            link_m = re.search(r'<link[^>]*>(.*?)</link>', item)
            desc_m = re.search(r'<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.DOTALL)
            pub_m = re.search(r'<pubDate>(.*?)</pubDate>', item)
            title_text = (title_m.group(1) or "").strip() if title_m else ""
            link_text = (link_m.group(1) or "").strip() if link_m else ""
            desc_text = re.sub(r'<[^>]+>', '', (desc_m.group(1) or "").strip())[:500] if desc_m else ""
            if not title_text:
                continue
            full_text = f"{title_text} {desc_text}"
            sentiment, score = keyword_sentiment(full_text)
            assets, currencies = detect_assets(full_text)
            impact = detect_impact(full_text, currencies)
            try:
                published = datetime.strptime(pub_m.group(1).strip(), "%a, %d %b %Y %H:%M:%S %z") if pub_m else datetime.now(timezone.utc)
            except Exception:
                published = datetime.now(timezone.utc)
            articles.append(NewsArticle(
                id=make_id(link_text or title_text),
                title=title_text, summary=desc_text, url=link_text,
                source=feed["source"], published_at=published,
                assets=assets, currencies=currencies,
                sentiment=sentiment, sentiment_score=score, impact=impact,
                keywords=extract_keywords(full_text), category=detect_category(full_text),
            ))
    except Exception as e:
        logger.warning(f"RSS {feed['source']} error: {e}")
    return articles


async def fetch_forex_factory(session: aiohttp.ClientSession) -> List[EconomicEvent]:
    events = []
    try:
        async with session.get(FOREX_FACTORY_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return events
            data = await resp.json(content_type=None)
        for item in data:
            impact_str = item.get("impact", "Low").lower()
            impact = Impact.HIGH if "high" in impact_str else (Impact.MEDIUM if "medium" in impact_str else Impact.LOW)
            currency = item.get("currency", "USD")
            sentiment, score = score_economic_event(item)
            try:
                event_time = datetime.fromisoformat(item.get("date", "").replace("Z", "+00:00"))
            except Exception:
                event_time = datetime.now(timezone.utc)
            def pf(v):
                try: return float(str(v).replace("%", "").strip()) if v else None
                except: return None
            actual = pf(item.get("actual"))
            forecast = pf(item.get("forecast"))
            previous = pf(item.get("previous"))
            surprise = (actual - forecast) if actual is not None and forecast is not None else None
            surprise_pct = round(surprise / abs(forecast) * 100, 2) if surprise is not None and forecast else None
            events.append(EconomicEvent(
                id=make_id(f"{item.get('date')}{item.get('title')}{currency}"),
                title=item.get("title", ""), currency=currency,
                country=CURRENCY_COUNTRIES.get(currency, currency),
                impact=impact, actual=actual, forecast=forecast, previous=previous,
                event_time=event_time, surprise=surprise, surprise_pct=surprise_pct,
                affected_assets=map_event_to_assets(currency),
                sentiment=sentiment, sentiment_score=score,
            ))
    except Exception as e:
        logger.warning(f"ForexFactory error: {e}")
    return events


class NewsStorage:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        self.db = self.client["market_lion"]
        self.articles_col = self.db["news_articles"]
        self.events_col = self.db["economic_events"]

    async def save_article(self, article: NewsArticle) -> bool:
        if await self.articles_col.find_one({"_id": article.id}):
            return False
        doc = asdict(article)
        doc["_id"] = doc.pop("id")
        doc["published_at"] = article.published_at.isoformat()
        doc["sentiment"] = article.sentiment.value
        doc["impact"] = article.impact.value
        await self.articles_col.insert_one(doc)
        return True

    async def save_event(self, event: EconomicEvent) -> bool:
        if await self.events_col.find_one({"_id": event.id}):
            return False
        doc = asdict(event)
        doc["_id"] = doc.pop("id")
        doc["event_time"] = event.event_time.isoformat()
        doc["sentiment"] = event.sentiment.value
        doc["impact"] = event.impact.value
        await self.events_col.insert_one(doc)
        return True

    async def get_recent_articles(self, asset: str = None, hours: int = 24, limit: int = 50) -> List[dict]:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        query: dict = {"published_at": {"$gte": since}}
        if asset:
            query["assets"] = asset
        return await self.articles_col.find(query).sort("published_at", -1).limit(limit).to_list(length=limit)

    async def get_upcoming_events(self, hours_ahead: int = 24) -> List[dict]:
        now = datetime.now(timezone.utc).isoformat()
        ahead = (datetime.now(timezone.utc) + timedelta(hours=hours_ahead)).isoformat()
        return await self.events_col.find({"event_time": {"$gte": now, "$lte": ahead}}).sort("event_time", 1).to_list(length=50)

    async def get_asset_sentiment(self, asset: str, hours: int = 4) -> dict:
        articles = await self.get_recent_articles(asset, hours)
        if not articles:
            return {"asset": asset, "sentiment": "NEUTRAL", "score": 0.0, "count": 0}
        scores = [a.get("sentiment_score", 0) for a in articles]
        avg = sum(scores) / len(scores)
        high_impact = sum(1 for a in articles if a.get("impact") == "HIGH")
        sentiment = "BULLISH" if avg > 0.1 else ("BEARISH" if avg < -0.1 else "NEUTRAL")
        return {"asset": asset, "sentiment": sentiment, "score": round(avg, 4),
                "count": len(articles), "high_impact_count": high_impact}


_storage: Optional[NewsStorage] = None
_kafka: Optional[AIOKafkaProducer] = None


async def get_storage():
    global _storage
    if _storage is None:
        _storage = NewsStorage()
    return _storage


async def get_kafka():
    global _kafka
    if _kafka is None:
        try:
            _kafka = AIOKafkaProducer(bootstrap_servers=KAFKA_URL)
            await _kafka.start()
        except Exception as e:
            logger.warning(f"Kafka unavailable: {e}")
            _kafka = None
    return _kafka


async def publish(topic: str, data: dict):
    producer = await get_kafka()
    if producer:
        try:
            await producer.send_and_wait(topic, json.dumps(data, default=str).encode())
        except Exception:
            pass


class NewsIngestionWorker:
    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def ingest_cycle(self) -> int:
        storage = await get_storage()
        new_count = 0
        async with aiohttp.ClientSession(headers={"User-Agent": "MarketLion/2.0"}) as session:
            rss_results = await asyncio.gather(*[parse_rss_feed(session, f) for f in RSS_FEEDS], return_exceptions=True)
            ff_events = await fetch_forex_factory(session)

        for result in rss_results:
            if isinstance(result, list):
                for article in result:
                    if await storage.save_article(article):
                        new_count += 1
                        if article.impact == Impact.HIGH:
                            await publish("market_news", {
                                "type": "news_high_impact", "id": article.id,
                                "title": article.title, "assets": article.assets,
                                "sentiment": article.sentiment, "score": article.sentiment_score,
                                "published_at": article.published_at.isoformat(),
                            })

        for event in ff_events:
            if await storage.save_event(event):
                if event.impact == Impact.HIGH:
                    await publish("economic_events", {
                        "type": "economic_event", "id": event.id, "title": event.title,
                        "currency": event.currency, "impact": event.impact,
                        "event_time": event.event_time.isoformat(), "sentiment": event.sentiment,
                        "score": event.sentiment_score, "affected_assets": event.affected_assets,
                        "surprise_pct": event.surprise_pct,
                    })

        logger.info(f"Ingestion: {new_count} new items")
        return new_count

    async def _loop(self, interval: int = 300):
        self.running = True
        while self.running:
            try:
                await self.ingest_cycle()
            except Exception as e:
                logger.error(f"Ingestion error: {e}")
            await asyncio.sleep(interval)

    def start(self):
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


_worker = NewsIngestionWorker()


@app.on_event("startup")
async def startup():
    _worker.start()


@app.on_event("shutdown")
async def shutdown():
    await _worker.stop()
    producer = await get_kafka()
    if producer:
        await producer.stop()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "news-ingestion"}


@app.get("/news/{asset}")
async def get_asset_news(asset: str, hours: int = 24, limit: int = 20):
    storage = await get_storage()
    articles = await storage.get_recent_articles(asset.upper(), hours, limit)
    return {"asset": asset.upper(), "articles": articles, "count": len(articles)}


@app.get("/sentiment/{asset}")
async def get_sentiment(asset: str, hours: int = 4):
    storage = await get_storage()
    return await storage.get_asset_sentiment(asset.upper(), hours)


@app.get("/sentiment/all")
async def get_all_sentiment(hours: int = 4):
    storage = await get_storage()
    assets = ["XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USOIL", "BTCUSD", "ETHUSD"]
    results = await asyncio.gather(*[storage.get_asset_sentiment(a, hours) for a in assets])
    return {"sentiments": list(results), "hours": hours}


@app.get("/calendar")
async def get_calendar(hours_ahead: int = 24):
    storage = await get_storage()
    events = await storage.get_upcoming_events(hours_ahead)
    return {"events": events, "count": len(events)}


@app.get("/calendar/high-impact")
async def get_high_impact(hours_ahead: int = 12):
    storage = await get_storage()
    events = await storage.get_upcoming_events(hours_ahead)
    high = [e for e in events if e.get("impact") == "HIGH"]
    return {"events": high, "count": len(high)}


@app.post("/ingest")
async def trigger_ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(_worker.ingest_cycle)
    return {"status": "triggered"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8007, reload=False)
