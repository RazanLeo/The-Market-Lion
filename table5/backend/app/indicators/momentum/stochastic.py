# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشر #15 — Stochastic Oscillator — Tier A
# الاستراتيجية: %K يقطع %D للأعلى في منطقة < 20 = شراء
#               %K يقطع %D للأسفل في منطقة > 80 = بيع
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


def _stoch_pandas(high: pd.Series, low: pd.Series, close: pd.Series,
                  k_period: int = 14, d_period: int = 3, smooth_k: int = 3):
    """Stochastic Slow fallback بدون TA-Lib"""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    raw_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    k = raw_k.rolling(window=smooth_k).mean()
    d = k.rolling(window=d_period).mean()
    return k, d


class StochasticIndicator(BaseIndicator):
    id = 15
    name = "Stochastic Oscillator"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "A"
    min_bars = 25

    def _compute(self, df: pd.DataFrame):
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)
        if HAS_TALIB:
            k, d = talib.STOCH(high.values, low.values, close.values,
                               fastk_period=14, slowk_period=3, slowk_matype=0,
                               slowd_period=3, slowd_matype=0)
            return pd.Series(k, index=close.index), pd.Series(d, index=close.index)
        return _stoch_pandas(high, low, close, 14, 3, 3)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        k, _ = self._compute(df)
        v = k.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        k, d = self._compute(df)
        if len(k) < 3 or pd.isna(k.iloc[-1]) or pd.isna(d.iloc[-1]):
            return "محايد"

        last_k, prev_k = k.iloc[-1], k.iloc[-2]
        last_d, prev_d = d.iloc[-1], d.iloc[-2]

        # تقاطع لأعلى في منطقة التشبع البيعي
        if prev_k <= prev_d and last_k > last_d and last_k < 30:
            return "شراء"
        # تقاطع لأسفل في منطقة التشبع الشرائي
        if prev_k >= prev_d and last_k < last_d and last_k > 70:
            return "بيع"
        # إشارات إضافية بدون تقاطع
        if last_k < 20 and last_k > prev_k:
            return "شراء"
        if last_k > 80 and last_k < prev_k:
            return "بيع"
        return "محايد"
