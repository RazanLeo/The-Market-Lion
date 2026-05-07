# ═══════════════════════════════════════════════════════════════════════════
# 🦁 سجل المؤشرات الـ 71 — Registry (المرجع: MarketLion_Indicators_Table.xlsx)
# الترقيم والـ Tier مطابقان حرفياً لـ db/seeds/006_indicators_71.sql
# ═══════════════════════════════════════════════════════════════════════════
from typing import List
import pandas as pd
from app.indicators.base import BaseIndicator

# ─── استيراد الكلاسات الموجودة (نستخدم منطقها الحسابي فقط) ──────────────────
from app.indicators.trend.moving_averages import (
    SMAIndicator as _SMA, EMAIndicator as _EMA, WMAIndicator as _WMA,
    HMAIndicator as _HMA, DEMAIndicator as _DEMA, TEMAIndicator as _TEMA,
    KAMAIndicator as _KAMA, T3Indicator as _T3, ALMAIndicator as _ALMA,
    ZLEMAIndicator as _ZLEMA, MAMAIndicator as _MAMA, SupertrendIndicator as _Super,
)
from app.indicators.momentum.rsi import RSIIndicator as _RSI
from app.indicators.momentum.macd import MACDIndicator as _MACD
from app.indicators.momentum.stochastic import StochasticIndicator as _Stoch
from app.indicators.momentum.adx_dmi import ADXDMIIndicator as _ADX
from app.indicators.momentum.extra import (
    CCIIndicator as _CCI, WilliamsRIndicator as _WR, MOMIndicator as _MOMcls,
    ROCIndicator as _ROC, TRIXIndicator as _TRIX, UltimateOscIndicator as _UO,
    StochRSIIndicator as _StochRSI, CMOIndicator as _CMO,
    AwesomeOscIndicator as _AO,
)
from app.indicators.volatility.bollinger import BollingerBandsIndicator as _BB
from app.indicators.volatility.atr import ATRIndicator as _ATR
from app.indicators.volatility.extra import (
    KeltnerChannelsIndicator as _KC, DonchianChannelsIndicator as _DC,
    StdDevIndicator as _SD, HistVolatilityIndicator as _HV,
    ChaikinVolIndicator as _CV, MassIndexIndicator as _MI,
    ChoppinessIndexIndicator as _CI,
)
from app.indicators.volume.obv import OBVIndicator as _OBV
from app.indicators.volume.extra import (
    VolumeIndicator as _Vol, ADIndicator as _AD, CMFIndicator as _CMF,
    MFIIndicator as _MFI, VWAPIndicator as _VWAP, EOMIndicator as _EOM,
    ForceIndexIndicator as _Force,
)
from app.indicators.support_resistance.all import (
    PivotPointsIndicator as _Pivot, FibonacciRetracementIndicator as _FibRet,
    FibonacciExtensionIndicator as _FibExt, TrendlineIndicator as _Trend,
)
from app.indicators.integrated.ichimoku import IchimokuIndicator as _Ichi
from app.indicators.integrated.extra import (
    ParabolicSARIndicator as _SAR, AroonIndicator as _Aroon,
    VortexIndicator as _Vortex, CoppockCurveIndicator as _Coppock,
)
from app.indicators.missing import (
    McGinleyIndicator as _MG, LinearRegressionIndicator as _LR,
    VolatilityStopIndicator as _VS, FRAMAIndicator as _FRAMA,
    VolatilityIndexIndicator as _VolIdx, ChaikinOscIndicator as _CO,
    KlingerOscIndicator as _Klinger, VolumeOscIndicator as _VO,
    PVIIndexIndicator as _PVI, NegativeVolIndex51 as _NVI,
    VWAPBasicIndicator as _VWAPB, AnchoredVWAPIndicator as _AVWAP,
    VolumeProfileVPVRIndicator as _VPVR, VWAPBandsIndicator as _VWAPBands,
    VolumeProfilePOCIndicator as _VPPOC, MarketProfileTPOIndicator as _MPTPO,
    CumulativeDeltaIndicator as _CDelta,
    FibFanIndicator as _FibFan, FibArcsIndicator as _FibArcs,
    FibTimeZonesIndicator as _FibTZ, FibSpeedFanIndicator as _FibSF,
    BollingerBPercentBandwidthIndicator as _BBPct,
    McClellanOscIndicator as _McClellan, ArmsTRINIndicator as _TRIN,
    AdvanceDeclineLineIndicator as _ADL,
)


# ─── Adapter ────────────────────────────────────────────────────────────────
def _make(canonical_id: int, name: str, category: str, category_en: str,
          tier: str, min_bars: int, base_cls):
    """يلفّ كلاسًا حسابيًا موجوداً بهوية المؤشر القانونية"""
    delegate_class = base_cls

    def __init__(self):
        BaseIndicator.__init__(self) if hasattr(BaseIndicator, "__init__") else None
        self._delegate = delegate_class()

    def compute_signal(self, df: pd.DataFrame) -> str:
        return self._delegate.compute_signal(df)

    def compute_raw_value(self, df: pd.DataFrame):
        try: return self._delegate.compute_raw_value(df)
        except Exception: return None

    cls = type(
        f"Indicator{canonical_id:02d}",
        (BaseIndicator,),
        {
            "id": canonical_id,
            "name": name,
            "category": category,
            "category_en": category_en,
            "tier": tier,
            "min_bars": min_bars,
            "__init__": __init__,
            "compute_signal": compute_signal,
            "compute_raw_value": compute_raw_value,
        },
    )
    return cls


# ─── الكتالوج الكامل (71) — مطابق لـ seed 006 ──────────────────────────────
# التصنيفات بالعربية
_TREND = ("مؤشرات الاتجاه", "Trend")
_MOM = ("مؤشرات الزخم", "Momentum")
_VOL_LIT = ("مؤشرات التذبذب والتقلب", "Volatility")
_VOLU = ("مؤشرات الحجم والتدفق", "Volume")
_SR = ("الدعم والمقاومة وفيبوناتشي", "Support/Resistance")
_INT = ("مؤشرات متكاملة", "Integrated")


CATALOG = [
    # Trend (1..12)
    (1,  "Parabolic SAR",                  _TREND, "B", 30, _SAR),
    (2,  "Supertrend",                     _TREND, "A", 30, _Super),
    (3,  "WMA",                            _TREND, "B", 60, _WMA),
    (4,  "HMA",                            _TREND, "B", 50, _HMA),
    (5,  "VWMA",                           _TREND, "B", 25, None),  # custom inline
    (6,  "DEMA",                           _TREND, "B", 60, _DEMA),
    (7,  "TEMA",                           _TREND, "B", 60, _TEMA),
    (8,  "KAMA",                           _TREND, "B", 60, _KAMA),
    (9,  "ALMA",                           _TREND, "B", 60, _ALMA),
    (10, "McGinley Dynamic",               _TREND, "B", 30, _MG),
    (11, "Linear Regression",              _TREND, "B", 30, _LR),
    (12, "Volatility Stop",                _TREND, "B", 30, _VS),
    # Momentum (13..28)
    (13, "RSI - Relative Strength Index",  _MOM,   "S", 30, _RSI),
    (14, "MACD - Moving Average Convergence Divergence", _MOM, "S", 35, _MACD),
    (15, "Stochastic Oscillator",          _MOM,   "A", 25, _Stoch),
    (16, "Stochastic RSI",                 _MOM,   "B", 35, _StochRSI),
    (17, "ADX + DMI",                      _MOM,   "S", 35, _ADX),
    (18, "CCI - Commodity Channel Index",  _MOM,   "B", 30, _CCI),
    (19, "Williams %R",                    _MOM,   "B", 25, _WR),
    (20, "ROC - Rate of Change",           _MOM,   "B", 25, _ROC),
    (21, "Momentum",                       _MOM,   "B", 25, _MOMcls),
    (22, "Awesome Oscillator",             _MOM,   "B", 40, _AO),
    (23, "Ultimate Oscillator",            _MOM,   "B", 35, _UO),
    (24, "TRIX",                           _MOM,   "B", 50, _TRIX),
    (25, "Aroon Indicator + Aroon Oscillator", _MOM, "B", 30, _Aroon),
    (26, "Vortex Indicator (VI)",          _MOM,   "B", 30, _Vortex),
    (27, "Coppock Curve",                  _MOM,   "C", 50, _Coppock),
    (28, "Chande Momentum Oscillator",     _MOM,   "B", 25, _CMO),
    # Volatility (29..39)
    (29, "Bollinger Bands",                _VOL_LIT, "S", 25, _BB),
    (30, "ATR",                            _VOL_LIT, "A", 25, _ATR),
    (31, "Keltner Channels",               _VOL_LIT, "B", 25, _KC),
    (32, "FRAMA",                          _VOL_LIT, "B", 30, _FRAMA),
    (33, "Donchian Channels",              _VOL_LIT, "B", 25, _DC),
    (34, "Standard Deviation",             _VOL_LIT, "B", 25, _SD),
    (35, "Historical Volatility",          _VOL_LIT, "B", 25, _HV),
    (36, "Choppiness Index",               _VOL_LIT, "A", 25, _CI),
    (37, "Chaikin Volatility",             _VOL_LIT, "C", 25, _CV),
    (38, "Mass Index",                     _VOL_LIT, "C", 30, _MI),
    (39, "Volatility Index",               _VOL_LIT, "C", 25, _VolIdx),
    # Volume (40..51)
    (40, "Volume (Normal)",                _VOLU,  "A", 25, _Vol),
    (41, "OBV - On Balance Volume",        _VOLU,  "A", 25, _OBV),
    (42, "MFI - Money Flow Index",         _VOLU,  "A", 25, _MFI),
    (43, "Accumulation / Distribution",    _VOLU,  "B", 25, _AD),
    (44, "Chaikin Money Flow",             _VOLU,  "B", 25, _CMF),
    (45, "Chaikin Oscillator",             _VOLU,  "B", 30, _CO),
    (46, "Klinger Oscillator",             _VOLU,  "B", 60, _Klinger),
    (47, "Force Index",                    _VOLU,  "B", 25, _Force),
    (48, "Ease of Movement",               _VOLU,  "B", 25, _EOM),
    (49, "Volume Oscillator",              _VOLU,  "C", 30, _VO),
    (50, "Positive / Negative Volume Index", _VOLU, "C", 100, _PVI),
    (51, "Negative Volume Index",          _VOLU,  "C", 100, _NVI),
    # VWAP / Volume Profile (52..58)
    (52, "VWAP (الأساسي)",                  _VOLU, "S", 20, _VWAPB),
    (53, "Anchored VWAP",                  _VOLU,  "A", 50, _AVWAP),
    (54, "Volume Profile (VPVR / VPSR)",   _VOLU,  "S", 50, _VPVR),
    (55, "VWAP with Standard Deviation Bands", _VOLU, "S", 30, _VWAPBands),
    (56, "Volume Profile with POC / HVN / LVN", _VOLU, "S", 50, _VPPOC),
    (57, "Market Profile (TPO)",           _VOLU,  "S", 50, _MPTPO),
    (58, "Cumulative Delta",               _VOLU,  "S", 30, _CDelta),
    # Support/Resistance / Fibonacci (59..66)
    (59, "Fibonacci Retracement",          _SR,    "S", 50, _FibRet),
    (60, "Pivot Points (Standard, Fibonacci, Camarilla, Woodie, DeMark)", _SR, "S", 25, _Pivot),
    (61, "Fibonacci Extension",            _SR,    "A", 50, _FibExt),
    (62, "Trend Lines",                    _SR,    "A", 30, _Trend),
    (63, "Fibonacci Fan",                  _SR,    "B", 50, _FibFan),
    (64, "Fibonacci Arcs",                 _SR,    "C", 50, _FibArcs),
    (65, "Fibonacci Time Zones",           _SR,    "C", 30, _FibTZ),
    (66, "Fibonacci Speed Resistance Fan", _SR,    "C", 50, _FibSF),
    # Integrated / Breadth (67..71)
    (67, "Ichimoku Cloud (Kinko Hyo)",     _INT,   "S", 60, _Ichi),
    (68, "Bollinger %B + Bandwidth",       _INT,   "A", 25, _BBPct),
    (69, "McClellan Oscillator",           _INT,   "C", 50, _McClellan),
    (70, "Arms Index (TRIN)",              _INT,   "C", 30, _TRIN),
    (71, "Advance / Decline Line",         _INT,   "C", 30, _ADL),
]


# ─── #5 VWMA — مؤشر مخصص inline ────────────────────────────────────────────
class _VWMACustom(BaseIndicator):
    id = 5; name = "VWMA"; category = "مؤشرات الاتجاه"; category_en = "Trend"
    tier = "B"; min_bars = 25

    def _vwma(self, df, period=20):
        import numpy as np
        c = df["close"].astype(float)
        if "volume" in df.columns and df["volume"].sum() > 0:
            v = df["volume"].astype(float)
            return (c * v).rolling(period).sum() / v.rolling(period).sum().replace(0, np.nan)
        return c.rolling(period).mean()

    def compute_raw_value(self, df):
        v = self._vwma(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df) -> str:
        c = df["close"].astype(float); vw = self._vwma(df)
        if pd.isna(vw.iloc[-1]): return "محايد"
        if c.iloc[-1] > vw.iloc[-1] and c.iloc[-2] <= vw.iloc[-2]: return "شراء"
        if c.iloc[-1] < vw.iloc[-1] and c.iloc[-2] >= vw.iloc[-2]: return "بيع"
        return "محايد"


# ─── البناء النهائي ─────────────────────────────────────────────────────────
def _build_classes():
    classes = []
    for entry in CATALOG:
        cid, name, (cat_ar, cat_en), tier, min_bars, base = entry
        if base is None:
            # خاص: VWMA #5
            cls = _VWMACustom
        else:
            cls = _make(cid, name, cat_ar, cat_en, tier, min_bars, base)
        classes.append(cls)
    return classes


_INDICATOR_CLASSES = _build_classes()


def get_all_71_indicators() -> List[BaseIndicator]:
    """يرجع كائنات الـ 71 مؤشر بالترتيب 1..71 — جميعها متطابقة مع الـ seed"""
    instances = [cls() for cls in _INDICATOR_CLASSES]
    assert len(instances) == 71, f"يجب أن يكون عدد المؤشرات 71، وُجد {len(instances)}"
    for expected_id, ind in enumerate(instances, start=1):
        assert ind.id == expected_id, f"خطأ في ترتيب id: متوقع {expected_id}، وُجد {ind.id} ({ind.name})"
    return instances


def verify_total_weight(tolerance: float = 1e-6) -> bool:
    total = sum(ind.weight for ind in get_all_71_indicators())
    if abs(total - 0.10) > tolerance:
        raise ValueError(
            f"إجمالي أوزان المؤشرات = {total:.10f} لا يساوي 0.10 — "
            "يجب أن يكون مجموع (S=4)×13 + (A=3)×11 + (B=2)×34 + (C=1)×13 = 166"
        )
    return True


def get_indicator_by_id(indicator_id: int) -> BaseIndicator:
    for ind in get_all_71_indicators():
        if ind.id == indicator_id:
            return ind
    raise KeyError(f"مؤشر ID={indicator_id} غير موجود")


def count_by_tier() -> dict:
    counts = {"S": 0, "A": 0, "B": 0, "C": 0}
    for ind in get_all_71_indicators():
        counts[ind.tier] += 1
    return counts


def count_by_category() -> dict:
    counts: dict = {}
    for ind in get_all_71_indicators():
        counts[ind.category] = counts.get(ind.category, 0) + 1
    return counts


if __name__ == "__main__":
    inds = get_all_71_indicators()
    print(f"✅ عدد المؤشرات = {len(inds)}")
    print(f"✅ التوزيع حسب Tier: {count_by_tier()}")
    print(f"✅ التوزيع حسب التصنيف: {count_by_category()}")
    verify_total_weight()
    total = sum(i.weight for i in inds)
    print(f"✅ إجمالي الأوزان = {total:.10f} ≈ 10٪")
