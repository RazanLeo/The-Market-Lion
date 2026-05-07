# ═══════════════════════════════════════════════════════════════════════════
# 🦁 أسد السوق — الفئة الأساسية للمؤشرات
# ═══════════════════════════════════════════════════════════════════════════
"""المؤشر الأساسي — كل مؤشر من الـ71 يرث منه"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone

import pandas as pd

from app.core.constants import (
    TIMEFRAME_WEIGHTS, TIMEFRAMES, SignalType, TierType,
    indicator_weight, signal_to_value, value_to_signal,
)


@dataclass
class IndicatorResult:
    """نتيجة مؤشر واحد على إطار زمني واحد"""
    indicator_id: int
    indicator_name: str
    timeframe: str
    signal: str          # شراء/بيع/محايد
    confidence: float    # 0..1 (per-TF بدائي)
    raw_value: Optional[float] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class IndicatorMultiTF:
    """نتيجة مؤشر واحد عبر كل الأطر الستة"""
    indicator_id: int
    indicator_name: str
    category: str
    tier: str
    weight: float                       # وزن من 0.10
    signals: dict[str, str]            # {"1M":"شراء", "5M":"بيع",...}
    weighted_score: float              # -1..+1
    confidence: float                  # 0..1 = abs(weighted_score)
    direction: str                     # القرار النهائي للمؤشر
    raw_values: dict[str, Optional[float]] = field(default_factory=dict)
    show_on_chart: bool = False        # تفضيل المستخدم (default OFF)


class BaseIndicator(ABC):
    """الفئة الأساسية لكل مؤشر فني"""

    # يجب على كل مؤشر أن يحدّد هذه
    id: int = 0                              # 1..71
    name: str = ""                           # الإنجليزية مطابقاً للـ Excel
    name_ar: str = ""                        # عربي اختياري
    category: str = ""                       # التصنيف بالعربي
    category_en: str = ""                    # التصنيف بالإنجليزي
    tier: str = "B"                          # S/A/B/C

    # الحد الأدنى لعدد الشموع المطلوبة (حسب فترة المؤشر)
    min_bars: int = 30

    @property
    def weight(self) -> float:
        """وزن المؤشر من 0.10 (10٪)"""
        return indicator_weight(self.tier)

    # ────────────────────────────────────────────────────────────────
    @abstractmethod
    def compute_signal(self, df: pd.DataFrame) -> str:
        """
        احسب الإشارة من DataFrame (timestamp, open, high, low, close, volume).
        أرجع: 'شراء' / 'بيع' / 'محايد'.
        """
        ...

    def compute_raw_value(self, df: pd.DataFrame) -> Optional[float]:
        """القيمة الخام للمؤشر (للعرض البصري). افتراضياً None."""
        return None

    # ────────────────────────────────────────────────────────────────
    def evaluate_all_timeframes(
        self,
        ohlcv_per_tf: dict[str, pd.DataFrame],
    ) -> IndicatorMultiTF:
        """
        احسب الإشارات على كل الأطر الستة + الدرجة الموزونة.

        ohlcv_per_tf = {"1M": df_1m, ..., "4H": df_4h}
        """
        signals: dict[str, str] = {}
        raw_values: dict[str, Optional[float]] = {}

        for tf in TIMEFRAMES:
            df = ohlcv_per_tf.get(tf)
            if df is None or len(df) < self.min_bars:
                signals[tf] = "محايد"
                raw_values[tf] = None
                continue
            try:
                sig = self.compute_signal(df)
                if sig not in ("شراء", "بيع", "محايد"):
                    sig = "محايد"
                signals[tf] = sig
                raw_values[tf] = self.compute_raw_value(df)
            except Exception:
                # أي خطأ في الحساب → محايد (لا نسقط الجدول كله)
                signals[tf] = "محايد"
                raw_values[tf] = None

        # الدرجة الموزونة عبر الأطر الستة (نطاق -1..+1)
        weighted = sum(
            signal_to_value(signals[tf]) * TIMEFRAME_WEIGHTS[tf]
            for tf in TIMEFRAMES
        ) / 100.0

        confidence = abs(weighted)
        direction = value_to_signal(weighted)

        return IndicatorMultiTF(
            indicator_id=self.id,
            indicator_name=self.name,
            category=self.category,
            tier=self.tier,
            weight=self.weight,
            signals=signals,
            weighted_score=weighted,
            confidence=confidence,
            direction=direction,
            raw_values=raw_values,
        )
