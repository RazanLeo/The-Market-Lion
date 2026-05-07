# ═══════════════════════════════════════════════════════════════════════════
# 🦁 خدمة بيانات السوق — جلب OHLCV على 6 أطر زمنية
# المصدر الأساسي: Capital.com (يُحقن عبر متغيرات بيئة)
# المصدر البديل: yfinance / ccxt / mock
# ═══════════════════════════════════════════════════════════════════════════
import os
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
import pandas as pd

from app.core.constants import TIMEFRAMES

logger = logging.getLogger(__name__)

# عدد الشموع المطلوبة لكل إطار (أكبر من min_bars الأكبر = 60)
BARS_PER_TF = 200

# تحويل أطر الجدول الخامس إلى صيغ Capital.com / yfinance
TF_TO_CAPITAL = {
    "1M": "MINUTE",
    "5M": "MINUTE_5",
    "15M": "MINUTE_15",
    "30M": "MINUTE_30",
    "1H": "HOUR",
    "4H": "HOUR_4",
}
TF_TO_YF = {
    "1M": ("1m", "5d"),
    "5M": ("5m", "10d"),
    "15M": ("15m", "30d"),
    "30M": ("30m", "60d"),
    "1H": ("60m", "60d"),
    "4H": ("4h", "180d"),
}
TF_DELTA = {
    "1M": timedelta(minutes=1),
    "5M": timedelta(minutes=5),
    "15M": timedelta(minutes=15),
    "30M": timedelta(minutes=30),
    "1H": timedelta(hours=1),
    "4H": timedelta(hours=4),
}


async def fetch_ohlcv_per_tf(symbol: str) -> dict[str, pd.DataFrame]:
    """
    أرجع dict {tf: DataFrame} لكل الأطر الستة.
    DataFrame columns: timestamp, open, high, low, close, volume
    """
    use_mock = os.environ.get("MARKET_DATA_SOURCE", "auto").lower() == "mock"

    if not use_mock:
        # 1. حاول Capital.com
        try:
            from app.services.capital_com import fetch_capital_ohlcv
            tasks = [fetch_capital_ohlcv(symbol, tf, BARS_PER_TF) for tf in TIMEFRAMES]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            out: dict[str, pd.DataFrame] = {}
            ok = True
            for tf, r in zip(TIMEFRAMES, results):
                if isinstance(r, Exception) or r is None or len(r) < 60:
                    ok = False; break
                out[tf] = r
            if ok:
                return out
            logger.warning("Capital.com فشل جزئياً، التبديل إلى yfinance")
        except Exception as e:
            logger.warning(f"Capital.com غير متوفر: {e}")

        # 2. حاول yfinance
        try:
            return await _fetch_via_yfinance(symbol)
        except Exception as e:
            logger.warning(f"yfinance فشل: {e}")

    # 3. Mock نهائي (للاختبار / التطوير)
    logger.warning(f"استخدام بيانات Mock لـ {symbol}")
    return _generate_mock(symbol)


# ─── yfinance ───────────────────────────────────────────────────────────────
async def _fetch_via_yfinance(symbol: str) -> dict[str, pd.DataFrame]:
    try:
        import yfinance as yf
    except ImportError:
        raise RuntimeError("yfinance غير مثبت")

    yf_symbol = symbol.replace("/", "")  # XAU/USD → XAUUSD (yfinance)
    if yf_symbol in ("XAUUSD",): yf_symbol = "XAUUSD=X"
    if yf_symbol in ("XTIUSD",): yf_symbol = "CL=F"

    out: dict[str, pd.DataFrame] = {}
    loop = asyncio.get_event_loop()
    for tf in TIMEFRAMES:
        interval, period = TF_TO_YF[tf]
        df = await loop.run_in_executor(None, lambda: yf.download(yf_symbol, interval=interval, period=period, progress=False, auto_adjust=False))
        if df is None or df.empty:
            raise RuntimeError(f"yfinance أرجع بيانات فارغة لـ {tf}")
        # Normalize columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df = df.rename(columns=str.lower)
        if "volume" not in df.columns: df["volume"] = 0.0
        df = df[["open", "high", "low", "close", "volume"]].dropna().tail(BARS_PER_TF).reset_index(drop=False)
        df = df.rename(columns={df.columns[0]: "timestamp"})
        out[tf] = df
    return out


# ─── Mock generator ─────────────────────────────────────────────────────────
def _generate_mock(symbol: str) -> dict[str, pd.DataFrame]:
    """يولّد بيانات OHLCV واقعية لاختبار محرك التصويت"""
    rng = np.random.default_rng(seed=hash(symbol) % (2**31))
    base_price = {"XAU/USD": 2050.0, "XTI/USD": 78.0, "EUR/USD": 1.08}.get(symbol, 100.0)

    out: dict[str, pd.DataFrame] = {}
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    for tf in TIMEFRAMES:
        delta = TF_DELTA[tf]
        n = BARS_PER_TF
        # Random walk لوغاريتمي
        log_ret = rng.normal(loc=0.0, scale=0.002, size=n)
        # نضيف ميل اتجاهي قليل
        trend = np.linspace(0, rng.normal(0, 0.01), n)
        prices = base_price * np.exp(np.cumsum(log_ret + trend))

        timestamps = [now - delta * (n - 1 - i) for i in range(n)]

        # OHLC من السعر (close) + تذبذب
        close = prices
        open_ = np.r_[close[0], close[:-1]]
        rand_vol = np.abs(rng.normal(0, 0.003, n)) * close
        high = np.maximum(open_, close) + rand_vol
        low = np.minimum(open_, close) - rand_vol
        volume = rng.uniform(1000, 10000, n)

        df = pd.DataFrame({
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
        out[tf] = df
    return out
