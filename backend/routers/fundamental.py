"""Fundamental analysis router: news, economic calendar, analysis summaries."""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Query

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fundamental", tags=["Fundamental Analysis"])

# ── Sample/fallback data ──────────────────────────────────────────────────────

SAMPLE_NEWS = [
    {
        "id": "1",
        "title": "Gold Surges Amid Fed Rate Cut Expectations",
        "title_ar": "الذهب يرتفع وسط توقعات خفض أسعار الفائدة الأمريكية",
        "source": "Reuters",
        "url": "https://www.reuters.com",
        "published_at": "2025-05-01T10:00:00Z",
        "sentiment": "bullish",
        "impact": "high",
        "symbols": ["XAU/USD"],
    },
    {
        "id": "2",
        "title": "EUR/USD Holds Near 1.08 as ECB Signals Gradual Easing",
        "title_ar": "اليورو/دولار يتماسك قرب 1.08 مع إشارات البنك الأوروبي لتيسير تدريجي",
        "source": "Bloomberg",
        "url": "https://www.bloomberg.com",
        "published_at": "2025-05-01T09:30:00Z",
        "sentiment": "neutral",
        "impact": "medium",
        "symbols": ["EUR/USD"],
    },
    {
        "id": "3",
        "title": "Oil Prices Climb on OPEC+ Production Cut Extension",
        "title_ar": "أسعار النفط ترتفع مع تمديد تخفيضات إنتاج أوبك+",
        "source": "Financial Times",
        "url": "https://www.ft.com",
        "published_at": "2025-05-01T08:15:00Z",
        "sentiment": "bullish",
        "impact": "high",
        "symbols": ["WTI/USD", "Brent/USD"],
    },
    {
        "id": "4",
        "title": "Bitcoin Tests $70K Resistance as Institutional Demand Grows",
        "title_ar": "البيتكوين يختبر مقاومة 70 ألف دولار مع نمو الطلب المؤسسي",
        "source": "CoinDesk",
        "url": "https://www.coindesk.com",
        "published_at": "2025-05-01T07:00:00Z",
        "sentiment": "bullish",
        "impact": "medium",
        "symbols": ["BTC/USD"],
    },
    {
        "id": "5",
        "title": "US Dollar Weakens on Soft Jobs Data",
        "title_ar": "الدولار الأمريكي يتراجع بسبب بيانات الوظائف الضعيفة",
        "source": "CNBC",
        "url": "https://www.cnbc.com",
        "published_at": "2025-04-30T18:00:00Z",
        "sentiment": "bearish",
        "impact": "high",
        "symbols": ["DXY", "EUR/USD", "GBP/USD"],
    },
]

SAMPLE_CALENDAR = [
    {
        "id": "ev1",
        "event": "Federal Reserve Interest Rate Decision",
        "event_ar": "قرار الفائدة من الاحتياطي الفيدرالي الأمريكي",
        "country": "US",
        "currency": "USD",
        "date": "2025-05-07T18:00:00Z",
        "impact": "high",
        "forecast": "5.25%",
        "previous": "5.50%",
        "actual": None,
    },
    {
        "id": "ev2",
        "event": "ECB Monetary Policy Statement",
        "event_ar": "بيان السياسة النقدية للبنك المركزي الأوروبي",
        "country": "EU",
        "currency": "EUR",
        "date": "2025-05-08T12:15:00Z",
        "impact": "high",
        "forecast": None,
        "previous": None,
        "actual": None,
    },
    {
        "id": "ev3",
        "event": "US Non-Farm Payrolls",
        "event_ar": "الرواتب غير الزراعية الأمريكية",
        "country": "US",
        "currency": "USD",
        "date": "2025-05-02T12:30:00Z",
        "impact": "high",
        "forecast": "200K",
        "previous": "303K",
        "actual": None,
    },
    {
        "id": "ev4",
        "event": "Bank of Japan Rate Decision",
        "event_ar": "قرار الفائدة من بنك اليابان",
        "country": "JP",
        "currency": "JPY",
        "date": "2025-05-09T03:00:00Z",
        "impact": "high",
        "forecast": "0.10%",
        "previous": "0.10%",
        "actual": None,
    },
    {
        "id": "ev5",
        "event": "US CPI (YoY)",
        "event_ar": "مؤشر أسعار المستهلكين الأمريكي (سنوي)",
        "country": "US",
        "currency": "USD",
        "date": "2025-05-14T12:30:00Z",
        "impact": "high",
        "forecast": "3.2%",
        "previous": "3.5%",
        "actual": None,
    },
]


# ── API fetchers ──────────────────────────────────────────────────────────────

async def _fetch_newsapi(query: str = "gold forex oil bitcoin trading") -> Optional[list]:
    if not settings.NEWS_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "apiKey": settings.NEWS_API_KEY,
                    "sortBy": "publishedAt",
                    "pageSize": 20,
                    "language": "en",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", [])
            news = []
            for i, a in enumerate(articles):
                news.append({
                    "id": str(i + 1),
                    "title": a.get("title", ""),
                    "title_ar": a.get("title", ""),  # Would use translation API
                    "source": a.get("source", {}).get("name", "NewsAPI"),
                    "url": a.get("url", ""),
                    "published_at": a.get("publishedAt", ""),
                    "sentiment": "neutral",
                    "impact": "medium",
                    "symbols": [],
                    "description": a.get("description", ""),
                })
            return news if news else None
    except Exception as e:
        logger.debug(f"NewsAPI fetch failed: {e}")
        return None


async def _fetch_alpha_vantage_news() -> Optional[list]:
    if not settings.ALPHA_VANTAGE_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "NEWS_SENTIMENT",
                    "tickers": "FOREX:EUR,FOREX:GBP,COMMODITY:GOLD,CRYPTO:BTC",
                    "limit": 20,
                    "apikey": settings.ALPHA_VANTAGE_KEY,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            feed = data.get("feed", [])
            news = []
            for i, item in enumerate(feed):
                sentiment_score = float(item.get("overall_sentiment_score", 0))
                sentiment = "bullish" if sentiment_score > 0.15 else "bearish" if sentiment_score < -0.15 else "neutral"
                news.append({
                    "id": f"av_{i}",
                    "title": item.get("title", ""),
                    "title_ar": item.get("title", ""),
                    "source": item.get("source", "Alpha Vantage"),
                    "url": item.get("url", ""),
                    "published_at": item.get("time_published", ""),
                    "sentiment": sentiment,
                    "impact": "medium",
                    "symbols": [],
                    "summary": item.get("summary", ""),
                })
            return news if news else None
    except Exception as e:
        logger.debug(f"Alpha Vantage news fetch failed: {e}")
        return None


async def _fetch_alpha_vantage_economic_calendar() -> Optional[list]:
    """Alpha Vantage economic calendar (uses ECONOMIC_CALENDAR endpoint if available)."""
    if not settings.ALPHA_VANTAGE_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "ECONOMIC_CALENDAR",
                    "apikey": settings.ALPHA_VANTAGE_KEY,
                    "horizon": "3month",
                },
            )
            if resp.status_code != 200:
                return None
            # Response is CSV
            text = resp.text
            if "Thank you for using Alpha Vantage" in text and "premium" in text.lower():
                return None
            lines = text.strip().split("\n")
            if len(lines) < 2:
                return None
            headers = lines[0].split(",")
            events = []
            for line in lines[1:21]:  # Limit to 20
                parts = line.split(",")
                if len(parts) < len(headers):
                    continue
                row = dict(zip(headers, parts))
                events.append({
                    "id": row.get("name", "")[:10].replace(" ", "_"),
                    "event": row.get("name", ""),
                    "event_ar": row.get("name", ""),
                    "country": row.get("country", "US"),
                    "currency": row.get("currency", "USD"),
                    "date": row.get("date", "") + "T12:00:00Z",
                    "impact": row.get("importance", "medium").lower(),
                    "forecast": row.get("estimate", None) or None,
                    "previous": row.get("previous", None) or None,
                    "actual": None,
                })
            return events if events else None
    except Exception as e:
        logger.debug(f"Alpha Vantage calendar fetch failed: {e}")
        return None


# ── Fundamental analysis helpers ──────────────────────────────────────────────

def _analyze_fundamental(symbol: str, news: list, calendar: list) -> dict:
    """Build a fundamental analysis summary for a symbol."""
    # Filter relevant news
    relevant_news = [n for n in news if symbol in n.get("symbols", [])]
    if not relevant_news:
        relevant_news = news[:3]  # Fallback to top 3

    sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
    for n in relevant_news:
        s = n.get("sentiment", "neutral")
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

    # Determine overall fundamental bias
    if sentiment_counts["bullish"] > sentiment_counts["bearish"]:
        bias = "bullish"
        bias_score = 0.7
    elif sentiment_counts["bearish"] > sentiment_counts["bullish"]:
        bias = "bearish"
        bias_score = 0.3
    else:
        bias = "neutral"
        bias_score = 0.5

    # Check for high-impact upcoming events
    high_impact_events = [e for e in calendar if e.get("impact") == "high"]

    return {
        "symbol": symbol,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fundamental_bias": bias,
        "bias_score": bias_score,
        "news_sentiment": sentiment_counts,
        "relevant_news_count": len(relevant_news),
        "upcoming_high_impact_events": len(high_impact_events),
        "key_drivers": _get_key_drivers(symbol),
        "summary": _get_fundamental_summary(symbol, bias),
        "summary_ar": _get_fundamental_summary_ar(symbol, bias),
    }


def _get_key_drivers(symbol: str) -> list:
    DRIVERS = {
        "XAU/USD": ["Fed interest rates", "USD strength", "Inflation data", "Geopolitical risk"],
        "XAG/USD": ["Industrial demand", "Fed policy", "Gold correlation"],
        "WTI/USD": ["OPEC+ production", "US inventories", "Global growth"],
        "Brent/USD": ["OPEC+ policy", "Middle East tensions", "Global demand"],
        "EUR/USD": ["ECB policy", "US CPI/NFP", "Eurozone PMI", "Fed vs ECB divergence"],
        "GBP/USD": ["BoE rate decisions", "UK inflation", "US data"],
        "USD/JPY": ["BoJ policy", "US yields", "Risk sentiment"],
        "BTC/USD": ["ETF flows", "Halving cycle", "Regulatory news", "Risk appetite"],
        "ETH/USD": ["Ethereum network upgrades", "DeFi activity", "BTC correlation"],
        "DXY": ["Fed policy", "US economic data", "Risk sentiment"],
    }
    return DRIVERS.get(symbol, ["Central bank policy", "Economic data", "Risk sentiment"])


def _get_fundamental_summary(symbol: str, bias: str) -> str:
    return (
        f"{symbol} shows {bias} fundamental outlook based on recent news sentiment "
        f"and upcoming economic events. Monitor central bank communications and "
        f"key economic releases for directional confirmation."
    )


def _get_fundamental_summary_ar(symbol: str, bias: str) -> str:
    BIAS_AR = {"bullish": "إيجابية", "bearish": "سلبية", "neutral": "محايدة"}
    return (
        f"{symbol} يُظهر نظرة أساسية {BIAS_AR.get(bias, 'محايدة')} بناءً على "
        f"تحليل الأخبار الأخيرة والأحداث الاقتصادية القادمة. "
        f"تابع قرارات البنوك المركزية والبيانات الاقتصادية الرئيسية للتأكيد."
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/news")
async def get_news(
    q: str = Query(default="gold forex oil bitcoin trading"),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Fetch latest financial news from NewsAPI or Alpha Vantage."""
    news = await _fetch_newsapi(q)
    if news is None:
        news = await _fetch_alpha_vantage_news()
    if news is None:
        news = SAMPLE_NEWS

    return {
        "news": news[:limit],
        "count": min(len(news), limit),
        "source": "live" if settings.NEWS_API_KEY or settings.ALPHA_VANTAGE_KEY else "sample",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/calendar")
async def get_economic_calendar():
    """Fetch upcoming economic calendar events."""
    calendar = await _fetch_alpha_vantage_economic_calendar()
    if calendar is None:
        calendar = SAMPLE_CALENDAR

    return {
        "events": calendar,
        "count": len(calendar),
        "source": "live" if settings.ALPHA_VANTAGE_KEY else "sample",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/analysis/{symbol:path}")
async def get_fundamental_analysis(symbol: str):
    """Get fundamental analysis summary for a symbol."""
    from routers.market_data import SUPPORTED_SYMBOLS
    symbol = symbol.upper().replace("%2F", "/")
    if symbol not in SUPPORTED_SYMBOLS:
        return {"error": f"Symbol {symbol} not supported"}

    # Fetch news and calendar in parallel
    news_resp = await get_news()
    cal_resp = await get_economic_calendar()

    news = news_resp.get("news", SAMPLE_NEWS)
    calendar = cal_resp.get("events", SAMPLE_CALENDAR)

    analysis = _analyze_fundamental(symbol, news, calendar)
    return analysis
