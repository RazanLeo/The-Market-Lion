# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشرات #52..#58 — Smart Money Concepts
# Order Block, Fair Value Gap, Liquidity Sweep, BOS, CHoCH, Equal Highs/Lows, Premium/Discount
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator


def _swing_highs(h: pd.Series, n: int = 5) -> pd.Series:
    """نقاط القمة المحلية (window=2n+1)"""
    rolling_max = h.rolling(window=2 * n + 1, center=True).max()
    return (h == rolling_max).astype(int)


def _swing_lows(l: pd.Series, n: int = 5) -> pd.Series:
    rolling_min = l.rolling(window=2 * n + 1, center=True).min()
    return (l == rolling_min).astype(int)


# ─────────────────────────────────────────────────────────────────────────────
class OrderBlockIndicator(BaseIndicator):
    """#52 — Order Block (آخر شمعة معاكسة قبل تحرّك قوي)"""
    id = 52
    name = "Order Block"
    category = "Smart Money"
    category_en = "Smart Money"
    tier = "S"
    min_bars = 30

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 20: return "محايد"
        c = df["close"].astype(float); o = df["open"].astype(float)
        h = df["high"].astype(float); l = df["low"].astype(float)
        # نبحث عن شمعة هابطة قبل سلسلة 3 شموع صاعدة (Bullish OB)
        for i in range(len(df) - 5, max(len(df) - 20, 5), -1):
            if c.iloc[i] < o.iloc[i] and all(c.iloc[i + j] > o.iloc[i + j] for j in range(1, 4)):
                # ob_low = l.iloc[i]; ob_high = h.iloc[i]
                if l.iloc[-1] >= l.iloc[i] and c.iloc[-1] > h.iloc[i]:
                    return "شراء"
            if c.iloc[i] > o.iloc[i] and all(c.iloc[i + j] < o.iloc[i + j] for j in range(1, 4)):
                if h.iloc[-1] <= h.iloc[i] and c.iloc[-1] < l.iloc[i]:
                    return "بيع"
        return "محايد"


class FairValueGapIndicator(BaseIndicator):
    """#53 — Fair Value Gap (FVG)"""
    id = 53
    name = "Fair Value Gap (FVG)"
    category = "Smart Money"
    category_en = "Smart Money"
    tier = "S"
    min_bars = 20

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 5: return "محايد"
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        # FVG صعودي: low[t] > high[t-2] (فجوة بين الشمعة الأولى والثالثة)
        for i in range(len(df) - 3, max(len(df) - 15, 2), -1):
            if l.iloc[i + 2] > h.iloc[i]:
                gap_top = l.iloc[i + 2]; gap_bot = h.iloc[i]
                # السعر الحالي عاد إلى منطقة الـ FVG
                if l.iloc[-1] <= gap_top and l.iloc[-1] >= gap_bot:
                    return "شراء"
            if h.iloc[i + 2] < l.iloc[i]:
                gap_top = l.iloc[i]; gap_bot = h.iloc[i + 2]
                if h.iloc[-1] >= gap_bot and h.iloc[-1] <= gap_top:
                    return "بيع"
        return "محايد"


class LiquiditySweepIndicator(BaseIndicator):
    """#54 — Liquidity Sweep / Stop Hunt"""
    id = 54
    name = "Liquidity Sweep"
    category = "Smart Money"
    category_en = "Smart Money"
    tier = "S"
    min_bars = 30

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 20: return "محايد"
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        # كنس سيولة فوق قمة سابقة ثم عودة (إشارة بيع) أو تحت قاع سابق ثم عودة (إشارة شراء)
        prev_high = h.iloc[-21:-1].max()
        prev_low = l.iloc[-21:-1].min()
        if h.iloc[-1] > prev_high and c.iloc[-1] < prev_high:
            return "بيع"
        if l.iloc[-1] < prev_low and c.iloc[-1] > prev_low:
            return "شراء"
        return "محايد"


class BreakOfStructureIndicator(BaseIndicator):
    """#55 — Break of Structure (BOS)"""
    id = 55
    name = "Break of Structure"
    category = "Smart Money"
    category_en = "Smart Money"
    tier = "S"
    min_bars = 30

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 20: return "محايد"
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        # كسر آخر قمة سابقة = BOS صعودي
        recent_high = h.iloc[-20:-2].max()
        recent_low = l.iloc[-20:-2].min()
        if c.iloc[-1] > recent_high: return "شراء"
        if c.iloc[-1] < recent_low: return "بيع"
        return "محايد"


class CHoCHIndicator(BaseIndicator):
    """#56 — Change of Character (CHoCH)"""
    id = 56
    name = "Change of Character"
    category = "Smart Money"
    category_en = "Smart Money"
    tier = "A"
    min_bars = 30

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 25: return "محايد"
        c = df["close"].astype(float)
        # CHoCH: تحول من اتجاه إلى آخر — نقيسه بسلوك EMA(20) و EMA(50)
        ema_short = c.ewm(span=20, adjust=False).mean()
        ema_long = c.ewm(span=50, adjust=False).mean()
        if pd.isna(ema_long.iloc[-1]): return "محايد"
        # تقاطع لأعلى بعد فترة هبوطية
        if ema_short.iloc[-2] <= ema_long.iloc[-2] and ema_short.iloc[-1] > ema_long.iloc[-1]:
            return "شراء"
        if ema_short.iloc[-2] >= ema_long.iloc[-2] and ema_short.iloc[-1] < ema_long.iloc[-1]:
            return "بيع"
        return "محايد"


class EqualHighsLowsIndicator(BaseIndicator):
    """#57 — Equal Highs/Lows (EQH/EQL)"""
    id = 57
    name = "Equal Highs/Lows"
    category = "Smart Money"
    category_en = "Smart Money"
    tier = "B"
    min_bars = 30

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 30: return "محايد"
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        recent_h = h.iloc[-30:].nlargest(3)
        recent_l = l.iloc[-30:].nsmallest(3)
        # قمم متساوية تقريباً = هدف سيولة قريب (احتمال انعكاس أو كسر)
        if (recent_h.max() - recent_h.min()) / recent_h.mean() < 0.003:
            if c.iloc[-1] > recent_h.mean(): return "شراء"  # كسرها
            return "بيع"  # ارتداد متوقع
        if (recent_l.max() - recent_l.min()) / recent_l.mean() < 0.003:
            if c.iloc[-1] < recent_l.mean(): return "بيع"
            return "شراء"
        return "محايد"


class PremiumDiscountIndicator(BaseIndicator):
    """#58 — Premium/Discount (Fibonacci Equilibrium)"""
    id = 58
    name = "Premium/Discount Zone"
    category = "Smart Money"
    category_en = "Smart Money"
    tier = "A"
    min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        if len(df) < 50: return None
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        rng_h = h.iloc[-50:].max(); rng_l = l.iloc[-50:].min()
        if rng_h == rng_l: return None
        return float((c.iloc[-1] - rng_l) / (rng_h - rng_l))

    def compute_signal(self, df: pd.DataFrame) -> str:
        v = self.compute_raw_value(df)
        if v is None: return "محايد"
        # Discount zone (< 0.382) = شراء، Premium (> 0.618) = بيع
        if v < 0.382: return "شراء"
        if v > 0.618: return "بيع"
        return "محايد"
