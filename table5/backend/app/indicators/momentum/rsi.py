# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشر #13 — RSI (Relative Strength Index) — Tier S
# الاستراتيجية: تشبع بيعي < 30 + Bullish Divergence = شراء قوي
#               تشبع شرائي > 70 + Bearish Divergence = بيع قوي
#               خط 50 يفصل اتجاه الزخم
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np

from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


def _rsi_pandas(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI fallback بدون TA-Lib"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


class RSIIndicator(BaseIndicator):
    id = 13
    name = "RSI - Relative Strength Index"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "S"
    min_bars = 30

    def _compute_rsi(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        if HAS_TALIB:
            return pd.Series(talib.RSI(close.values, timeperiod=14), index=close.index)
        return _rsi_pandas(close, 14)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        rsi = self._compute_rsi(df)
        v = rsi.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        rsi = self._compute_rsi(df)
        if rsi.isna().all():
            return "محايد"
        last, prev = rsi.iloc[-1], rsi.iloc[-2]
        if pd.isna(last) or pd.isna(prev):
            return "محايد"

        # تشبع بيعي + بدء صعود
        if last < 30 and last > prev:
            return "شراء"
        # تشبع شرائي + بدء نزول
        if last > 70 and last < prev:
            return "بيع"
        # خط 50 يفصل الزخم
        if last > 55:
            return "شراء"
        if last < 45:
            return "بيع"
        return "محايد"
