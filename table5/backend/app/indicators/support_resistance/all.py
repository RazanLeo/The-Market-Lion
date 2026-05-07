# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشرات #59..#66 — الدعم والمقاومة
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator


# ─────────────────────────────────────────────────────────────────────────────
class PivotPointsIndicator(BaseIndicator):
    """#59 — Classic Pivot Points"""
    id = 59
    name = "Pivot Points (Classic)"
    category = "الدعم والمقاومة"
    category_en = "Support/Resistance"
    tier = "A"
    min_bars = 25

    def _pivot(self, df: pd.DataFrame):
        if len(df) < 2: return None, None, None, None, None
        prev = df.iloc[-2]
        h, l, c = float(prev["high"]), float(prev["low"]), float(prev["close"])
        p = (h + l + c) / 3.0
        r1 = 2 * p - l; s1 = 2 * p - h
        r2 = p + (h - l); s2 = p - (h - l)
        return p, r1, s1, r2, s2

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        p, *_ = self._pivot(df)
        return float(p) if p is not None else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        p, r1, s1, r2, s2 = self._pivot(df)
        if p is None: return "محايد"
        c = float(df["close"].iloc[-1])
        if c > r1: return "شراء"
        if c < s1: return "بيع"
        if c > p: return "شراء"
        if c < p: return "بيع"
        return "محايد"


class FibonacciRetracementIndicator(BaseIndicator):
    """#60 — Fibonacci Retracement (auto)"""
    id = 60
    name = "Fibonacci Retracement"
    category = "الدعم والمقاومة"
    category_en = "Support/Resistance"
    tier = "A"
    min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        if len(df) < 50: return None
        h = df["high"].astype(float).iloc[-50:].max()
        l = df["low"].astype(float).iloc[-50:].min()
        c = float(df["close"].iloc[-1])
        if h == l: return None
        return float((c - l) / (h - l))

    def compute_signal(self, df: pd.DataFrame) -> str:
        v = self.compute_raw_value(df)
        if v is None: return "محايد"
        # عند مستويات فيبو الذهبية
        if 0.50 <= v <= 0.618: return "شراء"  # شراء عند تصحيح
        if v < 0.236: return "شراء"
        if v > 0.786: return "بيع"
        return "محايد"


class VolumeProfileVAIndicator(BaseIndicator):
    """#61 — Value Area High/Low"""
    id = 61
    name = "Value Area (VAH/VAL)"
    category = "الدعم والمقاومة"
    category_en = "Support/Resistance"
    tier = "B"
    min_bars = 50

    def _va(self, df: pd.DataFrame, bins: int = 50):
        if len(df) < 30: return None, None, None
        c = df["close"].astype(float).values
        if "volume" in df.columns and df["volume"].sum() > 0:
            v = df["volume"].astype(float).values
        else:
            v = np.ones_like(c)
        hist, edges = np.histogram(c, bins=bins, weights=v)
        if hist.sum() == 0: return None, None, None
        total = hist.sum() * 0.70
        idx = int(np.argmax(hist))
        accumulated = hist[idx]
        lo, hi = idx, idx
        while accumulated < total and (lo > 0 or hi < len(hist) - 1):
            left = hist[lo - 1] if lo > 0 else -1
            right = hist[hi + 1] if hi < len(hist) - 1 else -1
            if right >= left:
                hi += 1; accumulated += hist[hi]
            else:
                lo -= 1; accumulated += hist[lo]
        return float(edges[idx]), float(edges[hi + 1]), float(edges[lo])

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        poc, _, _ = self._va(df)
        return poc

    def compute_signal(self, df: pd.DataFrame) -> str:
        poc, vah, val = self._va(df)
        if poc is None: return "محايد"
        c = float(df["close"].iloc[-1])
        if c < val: return "شراء"  # تحت قيمة عادلة
        if c > vah: return "بيع"   # فوق قيمة عادلة
        return "محايد"


class CamarillaPivotsIndicator(BaseIndicator):
    """#62 — Camarilla Pivots"""
    id = 62
    name = "Camarilla Pivots"
    category = "الدعم والمقاومة"
    category_en = "Support/Resistance"
    tier = "B"
    min_bars = 25

    def _camarilla(self, df: pd.DataFrame):
        if len(df) < 2: return None
        prev = df.iloc[-2]
        h, l, c = float(prev["high"]), float(prev["low"]), float(prev["close"])
        rng = h - l
        return {
            "h4": c + rng * 1.1 / 2.0,
            "h3": c + rng * 1.1 / 4.0,
            "l3": c - rng * 1.1 / 4.0,
            "l4": c - rng * 1.1 / 2.0,
        }

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        cam = self._camarilla(df)
        if cam is None: return "محايد"
        c = float(df["close"].iloc[-1])
        if c > cam["h4"]: return "شراء"
        if c < cam["l4"]: return "بيع"
        if c < cam["l3"]: return "شراء"  # ارتداد من دعم
        if c > cam["h3"]: return "بيع"   # ارتداد من مقاومة
        return "محايد"


class WoodiePivotsIndicator(BaseIndicator):
    """#63 — Woodie's Pivots"""
    id = 63
    name = "Woodie's Pivots"
    category = "الدعم والمقاومة"
    category_en = "Support/Resistance"
    tier = "C"
    min_bars = 25

    def _wpiv(self, df: pd.DataFrame):
        if len(df) < 2: return None
        prev = df.iloc[-2]
        h, l, c = float(prev["high"]), float(prev["low"]), float(prev["close"])
        p = (h + l + 2 * c) / 4.0
        r1 = 2 * p - l; s1 = 2 * p - h
        return p, r1, s1

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        wp = self._wpiv(df)
        return wp[0] if wp else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        wp = self._wpiv(df)
        if wp is None: return "محايد"
        p, r1, s1 = wp
        c = float(df["close"].iloc[-1])
        if c > r1: return "شراء"
        if c < s1: return "بيع"
        return "محايد"


class FibonacciExtensionIndicator(BaseIndicator):
    """#64 — Fibonacci Extensions"""
    id = 64
    name = "Fibonacci Extension"
    category = "الدعم والمقاومة"
    category_en = "Support/Resistance"
    tier = "B"
    min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 50: return "محايد"
        h = df["high"].astype(float)
        l = df["low"].astype(float)
        c = df["close"].astype(float)
        # نأخذ آخر swing high/low ثم نحسب مدى الامتداد
        swing_h = h.iloc[-50:-10].max()
        swing_l = l.iloc[-50:-10].min()
        if swing_h == swing_l: return "محايد"
        rng = swing_h - swing_l
        ext_1618 = swing_h + rng * 0.618
        ext_neg_1618 = swing_l - rng * 0.618
        last = float(c.iloc[-1])
        if last >= ext_1618: return "بيع"  # امتداد كامل = هدف ربح
        if last <= ext_neg_1618: return "شراء"
        return "محايد"


class TrendlineIndicator(BaseIndicator):
    """#65 — Trendline (تقريبي)"""
    id = 65
    name = "Trendline"
    category = "الدعم والمقاومة"
    category_en = "Support/Resistance"
    tier = "B"
    min_bars = 30

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 30: return "محايد"
        c = df["close"].astype(float).iloc[-30:]
        x = np.arange(len(c))
        slope, intercept = np.polyfit(x, c.values, 1)
        last = float(c.iloc[-1])
        line_now = slope * (len(c) - 1) + intercept
        # السعر فوق خط الاتجاه + ميل صاعد = شراء
        if slope > 0 and last > line_now: return "شراء"
        if slope < 0 and last < line_now: return "بيع"
        return "محايد"


class HighsLowsIndicator(BaseIndicator):
    """#66 — Highs/Lows (52-bar)"""
    id = 66
    name = "Highs/Lows"
    category = "الدعم والمقاومة"
    category_en = "Support/Resistance"
    tier = "B"
    min_bars = 60

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 52: return "محايد"
        h = df["high"].astype(float)
        l = df["low"].astype(float)
        c = df["close"].astype(float)
        hh_52 = h.iloc[-52:].max()
        ll_52 = l.iloc[-52:].min()
        if c.iloc[-1] >= hh_52 * 0.998: return "شراء"  # قريب من قمة 52 بار
        if c.iloc[-1] <= ll_52 * 1.002: return "بيع"
        return "محايد"
