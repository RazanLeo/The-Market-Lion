# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشر #41 — OBV (On-Balance Volume) — Tier A
# الاستراتيجية: OBV صاعد + سعر صاعد = شراء (تأكيد حجمي)
#               OBV هابط + سعر هابط = بيع
#               تباعد OBV/سعر = إشارة انعكاس
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


def _obv_pandas(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum()


class OBVIndicator(BaseIndicator):
    id = 41
    name = "OBV - On-Balance Volume"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "A"
    min_bars = 25

    def _compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        volume = df["volume"].astype(float) if "volume" in df.columns else pd.Series([0.0] * len(df), index=close.index)
        if HAS_TALIB and "volume" in df.columns:
            return pd.Series(talib.OBV(close.values, volume.values), index=close.index)
        return _obv_pandas(close, volume)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        obv = self._compute(df)
        v = obv.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        obv = self._compute(df)
        close = df["close"].astype(float)
        if len(obv) < 20 or pd.isna(obv.iloc[-1]):
            return "محايد"

        # ميل OBV على آخر 10 شموع
        obv_slope = obv.iloc[-1] - obv.iloc[-10]
        price_slope = close.iloc[-1] - close.iloc[-10]

        if pd.isna(obv_slope) or pd.isna(price_slope):
            return "محايد"

        # تأكيد حجمي للاتجاه
        if obv_slope > 0 and price_slope > 0:
            return "شراء"
        if obv_slope < 0 and price_slope < 0:
            return "بيع"
        # تباعد إيجابي (OBV صاعد + سعر هابط) = شراء قادم
        if obv_slope > 0 and price_slope < 0:
            return "شراء"
        # تباعد سلبي (OBV هابط + سعر صاعد) = بيع قادم
        if obv_slope < 0 and price_slope > 0:
            return "بيع"
        return "محايد"
