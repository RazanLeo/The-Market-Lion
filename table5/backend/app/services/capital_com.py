# ═══════════════════════════════════════════════════════════════════════════
# 🦁 Capital.com adapter — جلب OHLCV عبر REST
# ═══════════════════════════════════════════════════════════════════════════
import os
import logging
from typing import Optional

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

CAPITAL_BASE = os.environ.get("CAPITAL_API_URL", "https://api-capital.backend-capital.com")
CAPITAL_KEY = os.environ.get("CAPITAL_API_KEY", "")
CAPITAL_LOGIN = os.environ.get("CAPITAL_LOGIN", "")
CAPITAL_PASSWORD = os.environ.get("CAPITAL_PASSWORD", "")

TF_MAP = {
    "1M": "MINUTE",
    "5M": "MINUTE_5",
    "15M": "MINUTE_15",
    "30M": "MINUTE_30",
    "1H": "HOUR",
    "4H": "HOUR_4",
}

_session_token: Optional[str] = None
_cst_token: Optional[str] = None


async def _ensure_session(client: httpx.AsyncClient):
    global _session_token, _cst_token
    if _session_token and _cst_token: return
    if not (CAPITAL_KEY and CAPITAL_LOGIN and CAPITAL_PASSWORD):
        raise RuntimeError("بيانات Capital.com غير مهيأة في environment")
    r = await client.post(
        f"{CAPITAL_BASE}/api/v1/session",
        headers={"X-CAP-API-KEY": CAPITAL_KEY, "Content-Type": "application/json"},
        json={"identifier": CAPITAL_LOGIN, "password": CAPITAL_PASSWORD},
    )
    r.raise_for_status()
    _session_token = r.headers.get("X-SECURITY-TOKEN")
    _cst_token = r.headers.get("CST")


async def fetch_capital_ohlcv(symbol: str, tf: str, bars: int = 200) -> Optional[pd.DataFrame]:
    """جلب شموع من Capital.com — يرجع DataFrame أو يرفع استثناء"""
    if tf not in TF_MAP:
        raise ValueError(f"إطار زمني غير معروف: {tf}")
    epic = symbol.replace("/", "")  # XAU/USD → XAUUSD
    async with httpx.AsyncClient(timeout=15.0) as client:
        await _ensure_session(client)
        url = f"{CAPITAL_BASE}/api/v1/prices/{epic}"
        params = {"resolution": TF_MAP[tf], "max": bars}
        headers = {
            "X-CAP-API-KEY": CAPITAL_KEY,
            "X-SECURITY-TOKEN": _session_token or "",
            "CST": _cst_token or "",
        }
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
        prices = data.get("prices") or []
        if not prices:
            return None
        rows = []
        for p in prices:
            o = p.get("openPrice") or {}
            h = p.get("highPrice") or {}
            l = p.get("lowPrice") or {}
            c = p.get("closePrice") or {}
            rows.append({
                "timestamp": p.get("snapshotTimeUTC") or p.get("snapshotTime"),
                "open": (o.get("bid", 0) + o.get("ask", 0)) / 2.0,
                "high": (h.get("bid", 0) + h.get("ask", 0)) / 2.0,
                "low":  (l.get("bid", 0) + l.get("ask", 0)) / 2.0,
                "close":(c.get("bid", 0) + c.get("ask", 0)) / 2.0,
                "volume": float(p.get("lastTradedVolume") or 0),
            })
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        df = df.dropna(subset=["timestamp"]).reset_index(drop=True)
        return df
