# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشر #29 — Bollinger Bands — Tier S
# الاستراتيجية: السعر يلامس النطاق السفلي + ارتداد = شراء
#               السعر يلامس النطاق العلوي + ارتداد = بيع
#               %B + Bandwidth (انضغاط النطاق) لرصد الانفجار القادم
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


def _bbands_pandas(close: pd.Series, period: int = 20, std_mult: float = 2.0):
    mid = close.rolling(window=period).mean()
    std = close.rolling(window=period).std(ddof=0)
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    return upper, mid, lower


class BollingerBandsIndicator(BaseIndicator):
    id = 29
    name = "Bollinger Bands"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "S"
    min_bars = 25

    def _compute(self, df: pd.DataFrame):
        close = df["close"].astype(float)
        if HAS_TALIB:
            upper, mid, lower = talib.BBANDS(close.values, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            return (pd.Series(upper, index=close.index),
                    pd.Series(mid, index=close.index),
                    pd.Series(lower, index=close.index))
        return _bbands_pandas(close, 20, 2.0)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        # %B = (close - lower) / (upper - lower) — مقياس موقع السعر داخل النطاق
        upper, _, lower = self._compute(df)
        close = df["close"].astype(float)
        denom = (upper.iloc[-1] - lower.iloc[-1])
        if denom == 0 or pd.isna(denom):
            return None
        pct_b = (close.iloc[-1] - lower.iloc[-1]) / denom
        return float(pct_b) if pd.notna(pct_b) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        upper, mid, lower = self._compute(df)
        close = df["close"].astype(float)
        if pd.isna(upper.iloc[-1]) or pd.isna(lower.iloc[-1]):
            return "محايد"

        last_close = close.iloc[-1]
        prev_close = close.iloc[-2]
        last_upper = upper.iloc[-1]
        last_lower = lower.iloc[-1]
        last_mid = mid.iloc[-1]

        # ارتداد من النطاق السفلي
        if prev_close <= lower.iloc[-2] and last_close > last_lower:
            return "شراء"
        # ارتداد من النطاق العلوي
        if prev_close >= upper.iloc[-2] and last_close < last_upper:
            return "بيع"
        # كسر فوق المتوسط مع زخم
        if last_close > last_mid and prev_close <= mid.iloc[-2]:
            return "شراء"
        if last_close < last_mid and prev_close >= mid.iloc[-2]:
            return "بيع"
        return "محايد"
