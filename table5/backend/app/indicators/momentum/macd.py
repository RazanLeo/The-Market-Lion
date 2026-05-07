# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشر #14 — MACD — Tier S
# الاستراتيجية: تقاطع MACD فوق الإشارة + هستوغرام موجب متزايد = شراء
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


class MACDIndicator(BaseIndicator):
    id = 14
    name = "MACD - Moving Average Convergence Divergence"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "S"
    min_bars = 35

    def _compute(self, df: pd.DataFrame):
        close = df["close"].astype(float)
        if HAS_TALIB:
            macd, sig, hist = talib.MACD(close.values, 12, 26, 9)
            return pd.Series(macd), pd.Series(sig), pd.Series(hist)
        ema12 = _ema(close, 12)
        ema26 = _ema(close, 26)
        macd = ema12 - ema26
        sig = _ema(macd, 9)
        hist = macd - sig
        return macd, sig, hist

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        _, _, hist = self._compute(df)
        v = hist.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        macd, sig, hist = self._compute(df)
        if len(macd) < 3 or pd.isna(macd.iloc[-1]) or pd.isna(hist.iloc[-2]):
            return "محايد"

        # شراء: تقاطع لأعلى + هستوغرام موجب متزايد
        if macd.iloc[-1] > sig.iloc[-1] and hist.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2]:
            return "شراء"
        # بيع: تقاطع لأسفل + هستوغرام سالب متزايد سلبياً
        if macd.iloc[-1] < sig.iloc[-1] and hist.iloc[-1] < 0 and hist.iloc[-1] < hist.iloc[-2]:
            return "بيع"
        return "محايد"
