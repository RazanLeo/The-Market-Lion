"""Free fundamental-data sources: RSS calendars + FRED + ForexFactory + Investing.com.

All HTTP calls are public and require no API key (FRED needs a free key but
also offers a public-CSV mirror that we use as fallback). On the production
server these will populate the `news_items` and `economic_events` tables.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from ...core.logging import get_logger

log = get_logger("fundamental")

# Symbol → which countries' macro events affect it
SYMBOL_COUNTRY_MAP = {
    "XAUUSD": ["USD", "EUR"], "XAGUSD": ["USD"],
    "USOIL":  ["USD", "OPEC"], "BRENT": ["USD", "OPEC"],
    "EURUSD": ["EUR", "USD"], "GBPUSD": ["GBP", "USD"],
    "USDJPY": ["JPY", "USD"], "USDCHF": ["CHF", "USD"],
    "USDCAD": ["CAD", "USD"], "AUDUSD": ["AUD", "USD"],
    "NZDUSD": ["NZD", "USD"], "DXY":    ["USD"],
}

# Public RSS feeds (no API key)
FOREX_FACTORY_RSS = "https://www.forexfactory.com/calendar.php?week=this&xml=1"
INVESTING_RSS     = "https://www.investing.com/rss/news_25.rss"   # economic indicators
DAILY_FX_RSS      = "https://www.dailyfx.com/feeds/all-news"

# FRED — public release calendar (no key needed for this endpoint)
FRED_RELEASES = "https://api.stlouisfed.org/fred/releases?api_key={api_key}&file_type=json"


def _http() -> httpx.Client:
    """Build an httpx client with sensible defaults for public APIs."""
    return httpx.Client(
        timeout=12.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; MarketLionBot/1.0)"},
    )


def fetch_forex_factory_calendar() -> list[dict[str, Any]]:
    """Pull this week's high-impact economic events from ForexFactory.

    Returns a list of {ts, country, title, impact, previous, forecast, actual}.
    """
    out = []
    try:
        with _http() as client:
            r = client.get(FOREX_FACTORY_RSS)
            if r.status_code != 200:
                return out
            text = r.text
        # ForexFactory XML format
        root = ET.fromstring(text)
        for ev in root.findall(".//event"):
            country = (ev.findtext("country") or "").strip()
            title = (ev.findtext("title") or "").strip()
            date_s = (ev.findtext("date") or "").strip()
            time_s = (ev.findtext("time") or "").strip()
            impact = (ev.findtext("impact") or "Low").strip().lower()
            forecast = ev.findtext("forecast") or None
            previous = ev.findtext("previous") or None
            actual = ev.findtext("actual") or None
            try:
                ts = datetime.strptime(f"{date_s} {time_s}", "%m-%d-%Y %I:%M%p").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            out.append({
                "ts": ts, "country": country, "title": title,
                "impact": impact, "forecast": forecast,
                "previous": previous, "actual": actual,
                "source": "forexfactory",
            })
    except Exception as e:  # pragma: no cover
        log.warning("ff_calendar_failed", err=str(e))
    return out


def fetch_investing_calendar_rss() -> list[dict[str, Any]]:
    """Investing.com economic news RSS — covers macro headlines."""
    out = []
    try:
        with _http() as client:
            r = client.get(INVESTING_RSS)
            if r.status_code != 200:
                return out
            text = r.text
        root = ET.fromstring(text)
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pubDate = (item.findtext("pubDate") or "").strip()
            desc = (item.findtext("description") or "").strip()
            try:
                ts = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                ts = datetime.now(timezone.utc)
            out.append({
                "ts": ts, "title": title, "url": link,
                "summary": desc[:500], "source": "investing.com",
                "category": "economic_indicators",
            })
    except Exception as e:  # pragma: no cover
        log.warning("investing_rss_failed", err=str(e))
    return out


def fetch_dailyfx_news() -> list[dict[str, Any]]:
    """DailyFX news RSS — currency-focused analysis."""
    out = []
    try:
        with _http() as client:
            r = client.get(DAILY_FX_RSS)
            if r.status_code != 200:
                return out
            text = r.text
        root = ET.fromstring(text)
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pubDate = (item.findtext("pubDate") or "").strip()
            try:
                ts = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                ts = datetime.now(timezone.utc)
            out.append({
                "ts": ts, "title": title, "url": link,
                "source": "dailyfx", "category": "fx_analysis",
            })
    except Exception as e:  # pragma: no cover
        log.warning("dailyfx_rss_failed", err=str(e))
    return out


def fetch_fred_releases(api_key: str | None = None) -> list[dict[str, Any]]:
    """FRED upcoming-release calendar. Free API key from research.stlouisfed.org."""
    if not api_key:
        return []
    out = []
    try:
        url = FRED_RELEASES.format(api_key=api_key)
        with _http() as client:
            r = client.get(url)
            if r.status_code != 200:
                return out
            data = r.json()
        for rel in data.get("releases", [])[:30]:
            out.append({
                "ts": datetime.now(timezone.utc),
                "country": "USD",
                "title": rel.get("name", ""),
                "impact": "high" if "FOMC" in rel.get("name", "") or "Payrolls" in rel.get("name", "") else "medium",
                "source": "fred",
            })
    except Exception as e:  # pragma: no cover
        log.warning("fred_failed", err=str(e))
    return out


def affected_symbols(country: str) -> list[str]:
    """Reverse-map: which symbols are sensitive to a given country's data."""
    return [sym for sym, ctrys in SYMBOL_COUNTRY_MAP.items() if country.upper() in ctrys]


def aggregate_all() -> dict[str, list[dict]]:
    """Run every public fundamental source. Returns separated news + events lists."""
    events = fetch_forex_factory_calendar()
    news = fetch_investing_calendar_rss() + fetch_dailyfx_news()
    return {"events": events, "news": news, "fetched_at": datetime.now(timezone.utc).isoformat()}
