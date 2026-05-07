# ═══════════════════════════════════════════════════════════════════════════
# 🦁 محرّك تصويت الجدول الخامس (الوزن 10٪)
# يجمع إشارات الـ 71 مؤشر عبر الأطر الستة ثم يطبّق:
#   1. الترجيح العادي (مؤشر × إطار)
#   2. Choppiness Filter (تخفيض الثقة عند ChoppinessIndex > 61.8)
#   3. HTF Veto (Tier S على 4H يفوق 1.5× المعارضة قصيرة المدى)
#   4. Tier S Convergence Boost (7+ مؤشرات S في نفس الاتجاه = +10٪ ثقة)
# ═══════════════════════════════════════════════════════════════════════════
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

from app.core.constants import (
    TIMEFRAMES, TIMEFRAME_WEIGHTS, DECISION_THRESHOLD,
    CHOPPINESS_FILTER_THRESHOLD, HTF_VETO_RATIO,
    signal_to_value, value_to_signal, signal_level,
)
from app.indicators.base import IndicatorMultiTF
from app.indicators.registry import get_all_71_indicators


@dataclass
class Table5Decision:
    """قرار الجدول الخامس النهائي"""
    symbol: str
    timestamp: str
    net_score: float            # -1..+1
    confidence: float           # 0..1
    decision: str               # شراء/بيع/محايد
    signal_level: str           # 👑 Crown / 🟢 قوية / 🟡 ضعيفة / ⚪
    indicators: list[IndicatorMultiTF] = field(default_factory=list)
    # تفاصيل الفلاتر المُطبَّقة
    choppiness_applied: bool = False
    htf_veto_applied: bool = False
    convergence_boost: bool = False
    tier_s_consensus: int = 0   # عدد Tier S الموافقة على الاتجاه


class Table5VotingEngine:
    """المحرك الرئيسي لجدول 5"""

    def __init__(self):
        self.indicators = get_all_71_indicators()
        # نخزّن مرجع لمؤشر Choppiness (#39) لاستخدامه كفلتر
        self._choppiness = next((i for i in self.indicators if i.id == 39), None)

    # ────────────────────────────────────────────────────────────────
    def evaluate(
        self,
        symbol: str,
        timestamp: str,
        ohlcv_per_tf: dict[str, pd.DataFrame],
    ) -> Table5Decision:
        """
        احسب القرار النهائي للجدول الخامس.
        ohlcv_per_tf = {"1M": df, "5M": df, "15M": df, "30M": df, "1H": df, "4H": df}
        """
        # الخطوة 1: حساب كل مؤشر عبر كل الأطر
        results: list[IndicatorMultiTF] = []
        for ind in self.indicators:
            results.append(ind.evaluate_all_timeframes(ohlcv_per_tf))

        # الخطوة 2: حساب الدرجة الصافية المرجحة
        net_score = 0.0
        for r in results:
            # وزن المؤشر × درجته الموزونة على الأطر
            net_score += r.weight * r.weighted_score
        # net_score الآن في نطاق -0.10..+0.10 (لأن مجموع الأوزان = 0.10)
        # نطبيعه إلى -1..+1
        normalized_score = net_score / 0.10

        # الخطوة 3: الثقة الأولية = القيمة المطلقة
        confidence = abs(normalized_score)
        decision = value_to_signal(normalized_score) if abs(normalized_score) >= DECISION_THRESHOLD else "محايد"

        # الخطوة 4: تطبيق Choppiness Filter
        choppiness_applied = self._apply_choppiness_filter(ohlcv_per_tf, decision)
        if choppiness_applied:
            confidence *= 0.5  # تخفيض الثقة 50٪

        # الخطوة 5: HTF Veto
        htf_veto_applied, htf_decision = self._apply_htf_veto(results, decision)
        if htf_veto_applied:
            decision = htf_decision

        # الخطوة 6: Tier S Convergence Boost
        tier_s_consensus, convergence_boost = self._apply_convergence_boost(results, decision)
        if convergence_boost:
            confidence = min(confidence * 1.10, 1.0)

        # الخطوة 7: تحديد المستوى النهائي
        level = signal_level(confidence)

        return Table5Decision(
            symbol=symbol,
            timestamp=timestamp,
            net_score=normalized_score,
            confidence=confidence,
            decision=decision,
            signal_level=level,
            indicators=results,
            choppiness_applied=choppiness_applied,
            htf_veto_applied=htf_veto_applied,
            convergence_boost=convergence_boost,
            tier_s_consensus=tier_s_consensus,
        )

    # ────────────────────────────────────────────────────────────────
    def _apply_choppiness_filter(
        self, ohlcv_per_tf: dict[str, pd.DataFrame], decision: str
    ) -> bool:
        """إذا Choppiness > 61.8 على إطار 1H → نخفض الثقة"""
        if self._choppiness is None: return False
        df_1h = ohlcv_per_tf.get("1H")
        if df_1h is None or len(df_1h) < self._choppiness.min_bars:
            return False
        try:
            ci_value = self._choppiness.compute_raw_value(df_1h)
            if ci_value is None: return False
            return ci_value > CHOPPINESS_FILTER_THRESHOLD
        except Exception:
            return False

    # ────────────────────────────────────────────────────────────────
    def _apply_htf_veto(
        self, results: list[IndicatorMultiTF], current_decision: str
    ) -> tuple[bool, str]:
        """
        إطار 4H للمؤشرات Tier S لا يُخالَف.
        إذا أغلبية Tier S على 4H تخالف القرار بنسبة HTF_VETO_RATIO → نقلب القرار.
        """
        tier_s = [r for r in results if r.tier == "S"]
        if not tier_s: return False, current_decision
        s_4h_signals = [r.signals.get("4H", "محايد") for r in tier_s]

        buys = s_4h_signals.count("شراء")
        sells = s_4h_signals.count("بيع")

        # القرار الحالي معاكس لاتجاه HTF S؟
        if current_decision == "شراء" and sells > buys * HTF_VETO_RATIO:
            return True, "بيع"
        if current_decision == "بيع" and buys > sells * HTF_VETO_RATIO:
            return True, "شراء"
        return False, current_decision

    # ────────────────────────────────────────────────────────────────
    def _apply_convergence_boost(
        self, results: list[IndicatorMultiTF], decision: str
    ) -> tuple[int, bool]:
        """7+ مؤشرات Tier S في نفس اتجاه القرار → boost +10٪"""
        if decision == "محايد": return 0, False
        tier_s = [r for r in results if r.tier == "S"]
        same_dir = [r for r in tier_s if r.direction == decision]
        return len(same_dir), len(same_dir) >= 7
