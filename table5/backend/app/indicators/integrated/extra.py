# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشرات #68..#71 — متكاملة (Integrated)
# Parabolic SAR, Aroon, Vortex, Coppock Curve
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


# ─────────────────────────────────────────────────────────────────────────────
class ParabolicSARIndicator(BaseIndicator):
    """#68 — Parabolic SAR"""
    id = 68
    name = "Parabolic SAR"
    category = "مؤشرات متكاملة"
    category_en = "Integrated"
    tier = "S"
    min_bars = 30

    def _sar(self, df: pd.DataFrame) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float)
        if HAS_TALIB:
            return pd.Series(talib.SAR(h.values, l.values, acceleration=0.02, maximum=0.20), index=df.index)
        # تنفيذ مبسط
        sar = pd.Series(index=df.index, dtype=float)
        af = 0.02; max_af = 0.20
        long = True
        ep = h.iloc[0]
        sar.iloc[0] = l.iloc[0]
        for i in range(1, len(df)):
            sar.iloc[i] = sar.iloc[i - 1] + af * (ep - sar.iloc[i - 1])
            if long:
                if l.iloc[i] < sar.iloc[i]:
                    long = False; sar.iloc[i] = ep; ep = l.iloc[i]; af = 0.02
                else:
                    if h.iloc[i] > ep: ep = h.iloc[i]; af = min(af + 0.02, max_af)
            else:
                if h.iloc[i] > sar.iloc[i]:
                    long = True; sar.iloc[i] = ep; ep = h.iloc[i]; af = 0.02
                else:
                    if l.iloc[i] < ep: ep = l.iloc[i]; af = min(af + 0.02, max_af)
        return sar

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._sar(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        sar = self._sar(df)
        c = df["close"].astype(float)
        if pd.isna(sar.iloc[-1]): return "محايد"
        if c.iloc[-1] > sar.iloc[-1]: return "شراء"
        if c.iloc[-1] < sar.iloc[-1]: return "بيع"
        return "محايد"


class AroonIndicator(BaseIndicator):
    """#69 — Aroon"""
    id = 69
    name = "Aroon"
    category = "مؤشرات متكاملة"
    category_en = "Integrated"
    tier = "B"
    min_bars = 30

    def _aroon(self, df: pd.DataFrame, period: int = 25):
        h = df["high"].astype(float); l = df["low"].astype(float)
        if HAS_TALIB:
            down, up = talib.AROON(h.values, l.values, timeperiod=period)
            return pd.Series(up, index=df.index), pd.Series(down, index=df.index)
        up = h.rolling(period + 1).apply(lambda x: 100 * (period - (period - np.argmax(x))) / period, raw=True)
        down = l.rolling(period + 1).apply(lambda x: 100 * (period - (period - np.argmin(x))) / period, raw=True)
        return up, down

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        up, down = self._aroon(df)
        v = up.iloc[-1] - down.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        up, down = self._aroon(df)
        if pd.isna(up.iloc[-1]) or pd.isna(down.iloc[-1]): return "محايد"
        if up.iloc[-1] > 70 and down.iloc[-1] < 30: return "شراء"
        if down.iloc[-1] > 70 and up.iloc[-1] < 30: return "بيع"
        return "محايد"


class VortexIndicator(BaseIndicator):
    """#70 — Vortex Indicator"""
    id = 70
    name = "Vortex Indicator"
    category = "مؤشرات متكاملة"
    category_en = "Integrated"
    tier = "B"
    min_bars = 30

    def _vortex(self, df: pd.DataFrame, period: int = 14):
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        vm_plus = (h - l.shift()).abs()
        vm_minus = (l - h.shift()).abs()
        sum_tr = tr.rolling(period).sum()
        vi_plus = vm_plus.rolling(period).sum() / sum_tr.replace(0, np.nan)
        vi_minus = vm_minus.rolling(period).sum() / sum_tr.replace(0, np.nan)
        return vi_plus, vi_minus

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        vp, vm = self._vortex(df)
        v = vp.iloc[-1] - vm.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        vp, vm = self._vortex(df)
        if pd.isna(vp.iloc[-1]): return "محايد"
        if vp.iloc[-1] > vm.iloc[-1] and vp.iloc[-2] <= vm.iloc[-2]: return "شراء"
        if vm.iloc[-1] > vp.iloc[-1] and vm.iloc[-2] <= vp.iloc[-2]: return "بيع"
        if vp.iloc[-1] > vm.iloc[-1] * 1.05: return "شراء"
        if vm.iloc[-1] > vp.iloc[-1] * 1.05: return "بيع"
        return "محايد"


class CoppockCurveIndicator(BaseIndicator):
    """#71 — Coppock Curve"""
    id = 71
    name = "Coppock Curve"
    category = "مؤشرات متكاملة"
    category_en = "Integrated"
    tier = "C"
    min_bars = 50

    def _coppock(self, c: pd.Series) -> pd.Series:
        roc14 = ((c - c.shift(14)) / c.shift(14)) * 100
        roc11 = ((c - c.shift(11)) / c.shift(11)) * 100
        sum_roc = roc14 + roc11
        # WMA(10)
        weights = np.arange(1, 11)
        return sum_roc.rolling(10).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._coppock(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        cop = self._coppock(c)
        if pd.isna(cop.iloc[-1]) or pd.isna(cop.iloc[-2]): return "محايد"
        # عبور الصفر صعوداً = شراء طويل المدى
        if cop.iloc[-2] <= 0 and cop.iloc[-1] > 0: return "شراء"
        if cop.iloc[-2] >= 0 and cop.iloc[-1] < 0: return "بيع"
        if cop.iloc[-1] > 0 and cop.iloc[-1] > cop.iloc[-2]: return "شراء"
        if cop.iloc[-1] < 0 and cop.iloc[-1] < cop.iloc[-2]: return "بيع"
        return "محايد"
