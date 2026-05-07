# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشر #67 — Ichimoku Cloud (سحابة إيشيموكو) — Tier S
# الاستراتيجية: السعر فوق السحابة + Tenkan > Kijun + Chikou فوق السعر = شراء قوي
#               السعر تحت السحابة + Tenkan < Kijun + Chikou تحت السعر = بيع قوي
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator


def _donchian_mid(high: pd.Series, low: pd.Series, period: int) -> pd.Series:
    """متوسط أعلى قمة وأدنى قاع خلال فترة"""
    return (high.rolling(window=period).max() + low.rolling(window=period).min()) / 2.0


class IchimokuIndicator(BaseIndicator):
    id = 67
    name = "Ichimoku Cloud"
    category = "مؤشرات متكاملة"
    category_en = "Integrated"
    tier = "S"
    min_bars = 60

    def _compute(self, df: pd.DataFrame):
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)

        # Tenkan-sen (خط التحول) — 9 periods
        tenkan = _donchian_mid(high, low, 9)
        # Kijun-sen (الخط القياسي) — 26 periods
        kijun = _donchian_mid(high, low, 26)
        # Senkou Span A (الحد العلوي للسحابة) — متوسط Tenkan & Kijun منزاح 26 للأمام
        senkou_a = ((tenkan + kijun) / 2.0).shift(26)
        # Senkou Span B (الحد السفلي للسحابة) — 52 periods منزاح 26
        senkou_b = _donchian_mid(high, low, 52).shift(26)
        # Chikou Span (الخط المتأخر) — close منزاح 26 للخلف
        chikou = close.shift(-26)

        return tenkan, kijun, senkou_a, senkou_b, chikou

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        # القيمة الخام = الفرق بين السعر ومنتصف السحابة (نسبة مئوية)
        tenkan, kijun, sa, sb, _ = self._compute(df)
        close = df["close"].astype(float)
        if pd.isna(sa.iloc[-1]) or pd.isna(sb.iloc[-1]):
            return None
        cloud_mid = (sa.iloc[-1] + sb.iloc[-1]) / 2.0
        if cloud_mid == 0:
            return None
        return float((close.iloc[-1] - cloud_mid) / cloud_mid * 100)

    def compute_signal(self, df: pd.DataFrame) -> str:
        tenkan, kijun, sa, sb, chikou = self._compute(df)
        close = df["close"].astype(float)
        if len(close) < 52 or pd.isna(tenkan.iloc[-1]) or pd.isna(kijun.iloc[-1]):
            return "محايد"
        if pd.isna(sa.iloc[-1]) or pd.isna(sb.iloc[-1]):
            return "محايد"

        last_close = close.iloc[-1]
        last_tk = tenkan.iloc[-1]
        last_kj = kijun.iloc[-1]
        cloud_top = max(sa.iloc[-1], sb.iloc[-1])
        cloud_bot = min(sa.iloc[-1], sb.iloc[-1])

        # شراء قوي: السعر فوق السحابة + Tenkan > Kijun
        if last_close > cloud_top and last_tk > last_kj:
            return "شراء"
        # بيع قوي: السعر تحت السحابة + Tenkan < Kijun
        if last_close < cloud_bot and last_tk < last_kj:
            return "بيع"
        # تقاطع داخل السحابة (إشارة ضعيفة)
        if last_tk > last_kj and last_close > last_kj:
            return "شراء"
        if last_tk < last_kj and last_close < last_kj:
            return "بيع"
        return "محايد"
