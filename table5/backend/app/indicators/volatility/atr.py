# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشر #30 — ATR (Average True Range) — Tier A
# الاستراتيجية: ATR لقياس التقلب فقط (لا يعطي اتجاه مباشر)
#               ATR صاعد + close > close[-period] = شراء (تقلب اتجاهي صاعد)
#               ATR صاعد + close < close[-period] = بيع
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


def _atr_pandas(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


class ATRIndicator(BaseIndicator):
    id = 30
    name = "ATR - Average True Range"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "A"
    min_bars = 25

    def _compute(self, df: pd.DataFrame) -> pd.Series:
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)
        if HAS_TALIB:
            return pd.Series(talib.ATR(high.values, low.values, close.values, timeperiod=14),
                             index=close.index)
        return _atr_pandas(high, low, close, 14)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        atr = self._compute(df)
        v = atr.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        atr = self._compute(df)
        close = df["close"].astype(float)
        if len(atr) < 15 or pd.isna(atr.iloc[-1]):
            return "محايد"

        # متوسط ATR على آخر 5 شموع مقارنةً بـ 5 سابقة
        atr_now = atr.iloc[-5:].mean()
        atr_prev = atr.iloc[-10:-5].mean()
        if pd.isna(atr_now) or pd.isna(atr_prev) or atr_prev == 0:
            return "محايد"

        atr_rising = atr_now > atr_prev * 1.05  # زيادة 5% على الأقل
        atr_falling = atr_now < atr_prev * 0.95

        # ATR صاعد + سعر صاعد = شراء (انفجار اتجاهي)
        price_change = close.iloc[-1] - close.iloc[-14]
        if atr_rising and price_change > 0:
            return "شراء"
        if atr_rising and price_change < 0:
            return "بيع"
        # ATR هابط = جانبي
        return "محايد"
