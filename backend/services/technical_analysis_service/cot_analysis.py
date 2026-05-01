"""Market Lion — COT (Commitment of Traders) Analysis.
Fetches CFTC weekly COT data and calculates net positioning, extremes, and bias.
Free source: https://www.cftc.gov/dea/newcot/
"""
import asyncio
import os
import logging
from datetime import datetime, timedelta, timezone
import aiohttp
import io

logger = logging.getLogger("cot-analysis")

# Futures contract codes mapped to CFTC market IDs
COT_MARKET_MAP = {
    "XAUUSD":  "088691",   # Gold
    "USOIL":   "067651",   # WTI Crude Oil
    "EURUSD":  "099741",   # Euro FX
    "GBPUSD":  "096742",   # British Pound
    "USDJPY":  "097741",   # Japanese Yen
    "AUDUSD":  "232741",   # Australian Dollar
    "CHFUSD":  "092741",   # Swiss Franc
    "CADUSD":  "090741",   # Canadian Dollar
    "BTCUSD":  "133741",   # Bitcoin
    "XAGUSD":  "084691",   # Silver
}

COT_COLUMNS = [
    "Market and Exchange Names", "As of Date in Form YYYY-MM-DD",
    "Open Interest (All)", "Noncommercial Positions-Long (All)",
    "Noncommercial Positions-Short (All)", "Commercial Positions-Long (All)",
    "Commercial Positions-Short (All)", "Nonreportable Positions-Long (All)",
    "Nonreportable Positions-Short (All)"
]


async def fetch_cot_data(year: int = None) -> str:
    """Download COT futures-only report from CFTC."""
    if year is None:
        year = datetime.now().year
    url = f"https://www.cftc.gov/dea/newcot/fut{year % 100:02d}.zip"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as sess:
            resp = await sess.get(url)
            if resp.status == 200:
                return await resp.read()
    except Exception as e:
        logger.error(f"COT fetch error: {e}")
    return None


def parse_cot_csv(raw_bytes: bytes, market_id: str) -> list[dict]:
    """Parse CFTC COT CSV for a specific market."""
    try:
        import zipfile
        import csv
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
            csv_file = [f for f in z.namelist() if f.endswith('.txt') or f.endswith('.csv')]
            if not csv_file:
                return []
            with z.open(csv_file[0]) as f:
                content = f.read().decode('latin-1')

        rows = []
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            if market_id in row.get("Market and Exchange Names", ""):
                rows.append({
                    "date": row.get("As of Date in Form YYYY-MM-DD", ""),
                    "open_interest": int(row.get("Open Interest (All)", 0) or 0),
                    "nc_long": int(row.get("Noncommercial Positions-Long (All)", 0) or 0),
                    "nc_short": int(row.get("Noncommercial Positions-Short (All)", 0) or 0),
                    "comm_long": int(row.get("Commercial Positions-Long (All)", 0) or 0),
                    "comm_short": int(row.get("Commercial Positions-Short (All)", 0) or 0),
                })
        return sorted(rows, key=lambda x: x["date"], reverse=True)
    except Exception as e:
        logger.error(f"COT parse error: {e}")
        return []


def calculate_cot_score(rows: list[dict]) -> dict:
    """Calculate COT sentiment score from positioning data."""
    if not rows:
        return {"signal": "NEUTRAL", "score": 0, "net_position": 0}

    latest = rows[0]
    nc_net = latest["nc_long"] - latest["nc_short"]   # Large specs (following trend)
    comm_net = latest["comm_long"] - latest["comm_short"]  # Commercials (contrarian)

    # Historical context (last 52 weeks)
    nc_nets = [r["nc_long"] - r["nc_short"] for r in rows[:52]]
    nc_max = max(nc_nets) if nc_nets else 1
    nc_min = min(nc_nets) if nc_nets else -1
    nc_range = nc_max - nc_min or 1

    # Normalized position index [0-100]
    nc_index = (nc_net - nc_min) / nc_range * 100

    # Extreme readings signal exhaustion (contrarian)
    if nc_index >= 85:
        signal = "SELL"      # speculators overly long → bearish exhaustion
        score = -0.7
    elif nc_index <= 15:
        signal = "BUY"       # speculators overly short → bullish exhaustion
        score = 0.7
    elif nc_index >= 65:
        signal = "BUY"       # trend continuation
        score = 0.5
    elif nc_index <= 35:
        signal = "SELL"
        score = -0.5
    else:
        signal = "NEUTRAL"
        score = 0.0

    # Week-over-week change
    if len(rows) >= 2:
        prev = rows[1]
        wow_change = nc_net - (prev["nc_long"] - prev["nc_short"])
    else:
        wow_change = 0

    return {
        "signal": signal,
        "score": round(score, 2),
        "net_position": nc_net,
        "nc_index": round(nc_index, 1),
        "nc_long": latest["nc_long"],
        "nc_short": latest["nc_short"],
        "comm_net": comm_net,
        "week_over_week": wow_change,
        "report_date": latest["date"],
    }


class COTService:
    def __init__(self):
        self._cache: dict = {}
        self._cache_time: dict = {}

    async def get_cot_score(self, symbol: str) -> dict:
        """Get COT sentiment score for a symbol."""
        market_id = COT_MARKET_MAP.get(symbol)
        if not market_id:
            return {"signal": "NEUTRAL", "score": 0, "note": "No COT data for this asset"}

        # Cache for 24 hours (COT is weekly)
        cache_key = f"cot_{symbol}"
        if cache_key in self._cache:
            age = (datetime.now(timezone.utc) - self._cache_time[cache_key]).total_seconds()
            if age < 86400:
                return self._cache[cache_key]

        # Try current year, fall back to previous
        for year_offset in [0, -1]:
            year = datetime.now().year + year_offset
            raw = await fetch_cot_data(year)
            if raw:
                rows = parse_cot_csv(raw, market_id)
                if rows:
                    result = calculate_cot_score(rows)
                    self._cache[cache_key] = result
                    self._cache_time[cache_key] = datetime.now(timezone.utc)
                    return result

        # Fallback: neutral
        return {"signal": "NEUTRAL", "score": 0, "note": "COT data unavailable"}


cot_service = COTService()
