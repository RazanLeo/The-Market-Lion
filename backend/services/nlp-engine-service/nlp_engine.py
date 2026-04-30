"""Market Lion — NLP Engine Service.
Pipeline: News Fetch → FinBERT Sentiment → Score → Cache in MongoDB + Redis.
Falls back to keyword-based scoring if no GPU / model not loaded.
"""
import asyncio
import os
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
import aiohttp
import json

logger = logging.getLogger("nlp-engine")

# ──────────────────────────────────────────────
# Keyword sentiment dictionaries
# ──────────────────────────────────────────────
BULLISH_WORDS = {
    "surge": 0.8, "rally": 0.8, "soar": 0.9, "jump": 0.7, "gain": 0.6,
    "rise": 0.5, "climb": 0.6, "boost": 0.7, "strengthen": 0.6, "recover": 0.5,
    "bullish": 0.9, "hawkish": 0.6, "beat": 0.7, "exceed": 0.7, "better": 0.5,
    "strong": 0.6, "robust": 0.7, "optimism": 0.7, "growth": 0.6, "profit": 0.6,
    "upgrade": 0.7, "buy": 0.5, "upside": 0.6, "outperform": 0.7, "record": 0.6,
    "stimulus": 0.7, "cut rates": 0.8, "rate cut": 0.8, "easing": 0.7,
}

BEARISH_WORDS = {
    "crash": -0.9, "collapse": -0.9, "plunge": -0.9, "fall": -0.7, "drop": -0.6,
    "slide": -0.6, "decline": -0.6, "lose": -0.6, "loss": -0.6, "weak": -0.6,
    "bearish": -0.9, "dovish": -0.5, "miss": -0.7, "below": -0.5, "worse": -0.6,
    "recession": -0.8, "slowdown": -0.7, "concern": -0.5, "fear": -0.7, "risk": -0.4,
    "downgrade": -0.7, "sell": -0.5, "downside": -0.6, "underperform": -0.7,
    "inflation": -0.5, "rate hike": -0.7, "hike": -0.6, "tightening": -0.6,
    "sanctions": -0.7, "war": -0.8, "conflict": -0.7, "crisis": -0.8,
}

# Asset-to-keyword mapping
ASSET_KEYWORDS = {
    "XAUUSD": ["gold", "xau", "precious metal", "safe haven", "fed", "inflation", "dollar"],
    "USOIL":  ["oil", "crude", "wti", "opec", "petroleum", "energy", "barrel"],
    "XBRUSD": ["brent", "crude", "opec", "energy", "oil"],
    "EURUSD": ["euro", "eur", "ecb", "eurozone", "europe", "german"],
    "GBPUSD": ["pound", "gbp", "boe", "bank of england", "uk", "britain"],
    "USDJPY": ["yen", "jpy", "boj", "bank of japan", "japan"],
    "AUDUSD": ["aud", "rba", "australia", "aussie", "china", "commodity"],
    "BTCUSD": ["bitcoin", "btc", "crypto", "cryptocurrency", "blockchain"],
}


def keyword_sentiment(text: str, asset: str) -> float:
    """Fast keyword-based sentiment score in [-1, 1]."""
    text_lower = text.lower()
    score = 0.0
    count = 0

    # Only score if text mentions the asset
    keywords = ASSET_KEYWORDS.get(asset, [])
    if not any(kw in text_lower for kw in keywords):
        return 0.0

    for word, weight in BULLISH_WORDS.items():
        if word in text_lower:
            score += weight
            count += 1
    for word, weight in BEARISH_WORDS.items():
        if word in text_lower:
            score += weight  # weight is negative
            count += 1

    return max(-1.0, min(1.0, score / max(count, 1)))


# ──────────────────────────────────────────────
# FinBERT (lazy-loaded)
# ──────────────────────────────────────────────
_finbert_pipeline = None

def get_finbert():
    global _finbert_pipeline
    if _finbert_pipeline is None:
        try:
            from transformers import pipeline
            _finbert_pipeline = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                device=-1,  # CPU
                max_length=512,
                truncation=True
            )
            logger.info("FinBERT loaded successfully")
        except Exception as e:
            logger.warning(f"FinBERT not available, using keyword scoring: {e}")
    return _finbert_pipeline


def finbert_score(text: str) -> float:
    """Returns score in [-1, 1] using FinBERT or fallback."""
    pipe = get_finbert()
    if pipe is None:
        return 0.0
    try:
        result = pipe(text[:512])[0]
        label = result["label"]  # positive / negative / neutral
        conf = result["score"]
        if label == "positive":
            return conf
        elif label == "negative":
            return -conf
        return 0.0
    except Exception:
        return 0.0


# ──────────────────────────────────────────────
# News Fetchers
# ──────────────────────────────────────────────
async def fetch_newsapi(query: str, api_key: str) -> list[dict]:
    if not api_key:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query, "sortBy": "publishedAt", "language": "en",
        "pageSize": 20, "apiKey": api_key,
        "from": (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
    }
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.get(url, params=params)
            data = await resp.json()
            return data.get("articles", [])
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
        return []


async def fetch_gnews(query: str) -> list[dict]:
    url = "https://gnews.io/api/v4/search"
    params = {"q": query, "lang": "en", "max": 10, "token": os.getenv("GNEWS_KEY", "")}
    if not params["token"]:
        return []
    try:
        async with aiohttp.ClientSession() as sess:
            resp = await sess.get(url, params=params)
            data = await resp.json()
            return [{"title": a["title"], "description": a["description"], "publishedAt": a["publishedAt"]}
                    for a in data.get("articles", [])]
    except Exception:
        return []


# ──────────────────────────────────────────────
# Main NLP Pipeline
# ──────────────────────────────────────────────
class NLPEngine:
    def __init__(self):
        self._redis = None
        self._mongo = None

    async def init(self):
        import redis.asyncio as aioredis
        self._redis = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
        )

    async def analyze_asset_sentiment(self, symbol: str) -> dict:
        cache_key = f"nlp_sentiment:{symbol}"
        if self._redis:
            cached = await self._redis.get(cache_key)
            if cached:
                return json.loads(cached)

        query_map = {
            "XAUUSD": "gold market outlook inflation fed",
            "USOIL": "crude oil WTI OPEC market",
            "EURUSD": "euro dollar ECB eurozone economy",
            "GBPUSD": "pound sterling bank of england UK economy",
            "USDJPY": "yen dollar BOJ Japan interest rates",
            "AUDUSD": "australian dollar RBA commodity prices",
            "BTCUSD": "bitcoin crypto market sentiment",
        }
        query = query_map.get(symbol, symbol.lower())

        articles = await fetch_newsapi(query, os.getenv("NEWSAPI_KEY", ""))
        if not articles:
            articles = await fetch_gnews(query)

        scores = []
        analyzed = []
        for art in articles[:20]:
            text = f"{art.get('title', '')} {art.get('description', '')}"
            ks = keyword_sentiment(text, symbol)
            fs = finbert_score(text)
            # Blend: 40% FinBERT + 60% keyword if FinBERT available, else 100% keyword
            pipe = get_finbert()
            final_score = (fs * 0.4 + ks * 0.6) if pipe else ks
            scores.append(final_score)
            analyzed.append({
                "title": art.get("title", "")[:120],
                "score": round(final_score, 3),
                "published": art.get("publishedAt", ""),
                "source": art.get("source", {}).get("name", "") if isinstance(art.get("source"), dict) else "",
            })

        avg_score = sum(scores) / len(scores) if scores else 0.0
        bullish_count = sum(1 for s in scores if s > 0.1)
        bearish_count = sum(1 for s in scores if s < -0.1)

        result = {
            "symbol": symbol,
            "sentiment_score": round(avg_score, 3),
            "direction": "BULLISH" if avg_score > 0.1 else ("BEARISH" if avg_score < -0.1 else "NEUTRAL"),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": len(scores) - bullish_count - bearish_count,
            "article_count": len(analyzed),
            "top_articles": sorted(analyzed, key=lambda x: abs(x["score"]), reverse=True)[:5],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if self._redis:
            await self._redis.setex(cache_key, 1800, json.dumps(result))

        return result


nlp_engine = NLPEngine()


async def main():
    await nlp_engine.init()
    logger.info("NLP Engine ready")
    # Test
    result = await nlp_engine.analyze_asset_sentiment("XAUUSD")
    logger.info(f"XAUUSD sentiment: {result['sentiment_score']} ({result['direction']})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
