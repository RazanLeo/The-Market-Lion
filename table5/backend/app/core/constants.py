# ═══════════════════════════════════════════════════════════════════════════
# 🦁 أسد السوق — ثوابت الجدول الخامس
# ═══════════════════════════════════════════════════════════════════════════
"""ثوابت محرك تصويت المؤشرات الفنية (الوزن 10٪ من القرار الكلي)"""
from typing import Literal

# نظام Tier (تصنيف قوة المؤشر)
TIER_VALUES: dict[str, int] = {
    "S": 4,   # مؤسسي جوهري
    "A": 3,   # موثوقية عالية
    "B": 2,   # داعم صلب
    "C": 1,   # تخصصي نادر
}

# 13×4 + 11×3 + 34×2 + 13×1 = 166
TOTAL_TIER_SUM: int = 166

# توزيع الـ71 مؤشر على Tiers
TIER_S_COUNT: int = 13
TIER_A_COUNT: int = 11
TIER_B_COUNT: int = 34
TIER_C_COUNT: int = 13

# أوزان الأطر الزمنية (المجموع = 100)
TIMEFRAME_WEIGHTS: dict[str, int] = {
    "1M":   5,    # المحفّز اللحظي
    "5M":  10,    # إطار التنفيذ
    "15M": 20,    # إطار التداول الرئيسي
    "30M": 18,    # السياق المباشر
    "1H":  22,    # الإطار المرجعي للاتجاه
    "4H":  25,    # الإطار المرجعي الأكبر — لا يُخالَف
}

# عتبات الإشارة
SIGNAL_THRESHOLDS: dict[str, float] = {
    "crown":  0.80,   # 👑 إشارة التاج
    "strong": 0.60,   # 🟢 قوية
    "weak":   0.30,   # 🟡 ضعيفة
    "none":   0.00,   # ⚪ لا إشارة
}

# عتبة قرار الإطار الزمني (0.5%)
DECISION_THRESHOLD: float = 0.005

# قائمة الأطر الزمنية (الترتيب مهم)
TIMEFRAMES: list[str] = ["1M", "5M", "15M", "30M", "1H", "4H"]

# نوع الإشارة
SignalType = Literal["شراء", "بيع", "محايد"]
TierType = Literal["S", "A", "B", "C"]

# قاعدة Choppiness Filter
CHOPPINESS_FILTER_THRESHOLD: float = 61.8

# قاعدة HTF Veto (الإطار الأعلى لا يُخالَف)
HTF_VETO_RATIO: float = 1.5


def indicator_weight(tier: str) -> float:
    """يرجع وزن المؤشر من إجمالي الـ 10٪ كنسبة من 1.0"""
    if tier not in TIER_VALUES:
        raise ValueError(f"Tier غير معروف: {tier}")
    return (TIER_VALUES[tier] / TOTAL_TIER_SUM) * 0.10


def signal_to_value(signal: str) -> int:
    """تحويل الإشارة لقيمة عددية للحساب"""
    return {"شراء": 1, "بيع": -1, "محايد": 0}.get(signal, 0)


def value_to_signal(value: float) -> str:
    """تحويل القيمة لإشارة"""
    if value > 0: return "شراء"
    if value < 0: return "بيع"
    return "محايد"


def signal_level(confidence: float) -> str:
    """تحديد مستوى الإشارة من قيمة الثقة"""
    if confidence >= SIGNAL_THRESHOLDS["crown"]:  return "👑 Crown"
    if confidence >= SIGNAL_THRESHOLDS["strong"]: return "🟢 قوية"
    if confidence >= SIGNAL_THRESHOLDS["weak"]:   return "🟡 ضعيفة"
    return "⚪ لا إشارة"
