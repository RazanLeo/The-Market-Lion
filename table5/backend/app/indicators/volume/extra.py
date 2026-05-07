# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشرات #40، #42..#51 — مؤشرات الحجم الإضافية
# ملاحظة: في حالة عدم توفر volume، نُرجع "محايد" بأمان
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


def _ema(s: pd.Series, p: int) -> pd.Series:
    return s.ewm(span=p, adjust=False).mean()


def _has_volume(df: pd.DataFrame) -> bool:
    if "volume" not in df.columns: return False
    return df["volume"].sum() > 0


# ─────────────────────────────────────────────────────────────────────────────
class VolumeIndicator(BaseIndicator):
    """#40 — Volume (Raw)"""
    id = 40
    name = "Volume"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "B"
    min_bars = 25

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        if not _has_volume(df): return None
        v = df["volume"].iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if not _has_volume(df): return "محايد"
        c = df["close"].astype(float); v = df["volume"].astype(float)
        avg_v = v.rolling(20).mean()
        if pd.isna(avg_v.iloc[-1]): return "محايد"
        # حجم > 1.5× المتوسط + سعر صاعد = شراء
        if v.iloc[-1] > avg_v.iloc[-1] * 1.5 and c.iloc[-1] > c.iloc[-2]: return "شراء"
        if v.iloc[-1] > avg_v.iloc[-1] * 1.5 and c.iloc[-1] < c.iloc[-2]: return "بيع"
        return "محايد"


class ADIndicator(BaseIndicator):
    """#42 — Accumulation/Distribution Line"""
    id = 42
    name = "A/D - Accumulation/Distribution Line"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "B"
    min_bars = 25

    def _ad(self, df: pd.DataFrame) -> pd.Series:
        if not _has_volume(df): return pd.Series([0.0] * len(df), index=df.index)
        h = df["high"].astype(float); l = df["low"].astype(float)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        if HAS_TALIB:
            return pd.Series(talib.AD(h.values, l.values, c.values, v.values), index=df.index)
        clv = ((c - l) - (h - c)) / (h - l).replace(0, np.nan)
        return (clv * v).cumsum()

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._ad(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if not _has_volume(df): return "محايد"
        ad = self._ad(df)
        c = df["close"].astype(float)
        if pd.isna(ad.iloc[-1]) or len(ad) < 11: return "محايد"
        ad_up = ad.iloc[-1] > ad.iloc[-10]
        price_up = c.iloc[-1] > c.iloc[-10]
        if ad_up and price_up: return "شراء"
        if not ad_up and not price_up: return "بيع"
        return "محايد"


class CMFIndicator(BaseIndicator):
    """#43 — Chaikin Money Flow"""
    id = 43
    name = "CMF - Chaikin Money Flow"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "A"
    min_bars = 25

    def _cmf(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        if not _has_volume(df): return pd.Series([0.0] * len(df), index=df.index)
        h = df["high"].astype(float); l = df["low"].astype(float)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        mfm = ((c - l) - (h - c)) / (h - l).replace(0, np.nan)
        mfv = mfm * v
        return mfv.rolling(period).sum() / v.rolling(period).sum().replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._cmf(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if not _has_volume(df): return "محايد"
        cmf = self._cmf(df)
        if pd.isna(cmf.iloc[-1]): return "محايد"
        if cmf.iloc[-1] > 0.10: return "شراء"
        if cmf.iloc[-1] < -0.10: return "بيع"
        return "محايد"


class MFIIndicator(BaseIndicator):
    """#44 — Money Flow Index"""
    id = 44
    name = "MFI - Money Flow Index"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "A"
    min_bars = 25

    def _mfi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        if not _has_volume(df): return pd.Series([50.0] * len(df), index=df.index)
        h = df["high"].astype(float); l = df["low"].astype(float)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        if HAS_TALIB:
            return pd.Series(talib.MFI(h.values, l.values, c.values, v.values, timeperiod=period), index=df.index)
        tp = (h + l + c) / 3.0
        mf = tp * v
        delta = tp.diff()
        pos_mf = mf.where(delta > 0, 0.0).rolling(period).sum()
        neg_mf = mf.where(delta < 0, 0.0).rolling(period).sum().abs()
        ratio = pos_mf / neg_mf.replace(0, np.nan)
        return 100 - (100 / (1 + ratio))

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._mfi(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if not _has_volume(df): return "محايد"
        m = self._mfi(df)
        if pd.isna(m.iloc[-1]): return "محايد"
        last, prev = m.iloc[-1], m.iloc[-2]
        if last < 20 and last > prev: return "شراء"
        if last > 80 and last < prev: return "بيع"
        return "محايد"


class VWAPIndicator(BaseIndicator):
    """#45 — VWAP"""
    id = 45
    name = "VWAP - Volume Weighted Average Price"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "S"
    min_bars = 20

    def _vwap(self, df: pd.DataFrame) -> pd.Series:
        if not _has_volume(df):
            c = df["close"].astype(float)
            return c.rolling(20).mean()
        h = df["high"].astype(float); l = df["low"].astype(float)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        tp = (h + l + c) / 3.0
        cum_vol = v.cumsum()
        cum_pv = (tp * v).cumsum()
        return cum_pv / cum_vol.replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._vwap(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        vwap = self._vwap(df)
        c = df["close"].astype(float)
        if pd.isna(vwap.iloc[-1]): return "محايد"
        if c.iloc[-1] > vwap.iloc[-1] and c.iloc[-2] <= vwap.iloc[-2]: return "شراء"
        if c.iloc[-1] < vwap.iloc[-1] and c.iloc[-2] >= vwap.iloc[-2]: return "بيع"
        if c.iloc[-1] > vwap.iloc[-1] * 1.005: return "شراء"
        if c.iloc[-1] < vwap.iloc[-1] * 0.995: return "بيع"
        return "محايد"


class VolumeProfileIndicator(BaseIndicator):
    """#46 — Volume Profile (POC)"""
    id = 46
    name = "Volume Profile (POC)"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "A"
    min_bars = 50

    def _poc(self, df: pd.DataFrame, bins: int = 50) -> float:
        if not _has_volume(df) or len(df) < 20: return None
        c = df["close"].astype(float).values
        v = df["volume"].astype(float).values
        hist, edges = np.histogram(c, bins=bins, weights=v)
        if hist.sum() == 0: return None
        idx = int(np.argmax(hist))
        return float((edges[idx] + edges[idx + 1]) / 2.0)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return self._poc(df)

    def compute_signal(self, df: pd.DataFrame) -> str:
        poc = self._poc(df)
        if poc is None: return "محايد"
        c = df["close"].astype(float)
        last = c.iloc[-1]
        # ارتداد من POC يعتبر فرصة
        if abs(last - poc) / poc < 0.002:
            # السعر عند POC — انتظر اتجاه
            return "محايد"
        if last > poc * 1.005: return "شراء"
        if last < poc * 0.995: return "بيع"
        return "محايد"


class VWMAIndicator(BaseIndicator):
    """#47 — Volume Weighted Moving Average"""
    id = 47
    name = "VWMA - Volume Weighted MA"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "B"
    min_bars = 25

    def _vwma(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        c = df["close"].astype(float)
        if not _has_volume(df):
            return c.rolling(period).mean()
        v = df["volume"].astype(float)
        return (c * v).rolling(period).sum() / v.rolling(period).sum().replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._vwma(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        vw = self._vwma(df)
        c = df["close"].astype(float)
        if pd.isna(vw.iloc[-1]): return "محايد"
        if c.iloc[-1] > vw.iloc[-1] and c.iloc[-2] <= vw.iloc[-2]: return "شراء"
        if c.iloc[-1] < vw.iloc[-1] and c.iloc[-2] >= vw.iloc[-2]: return "بيع"
        return "محايد"


class EOMIndicator(BaseIndicator):
    """#48 — Ease of Movement"""
    id = 48
    name = "EOM - Ease of Movement"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "C"
    min_bars = 25

    def _eom(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        if not _has_volume(df): return pd.Series([0.0] * len(df), index=df.index)
        h = df["high"].astype(float); l = df["low"].astype(float)
        v = df["volume"].astype(float)
        midpoint = ((h + l) / 2.0).diff()
        box = v / 100000000.0 / (h - l).replace(0, np.nan)
        return (midpoint / box.replace(0, np.nan)).rolling(period).mean()

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._eom(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if not _has_volume(df): return "محايد"
        e = self._eom(df)
        if pd.isna(e.iloc[-1]): return "محايد"
        if e.iloc[-1] > 0 and e.iloc[-1] > e.iloc[-2]: return "شراء"
        if e.iloc[-1] < 0 and e.iloc[-1] < e.iloc[-2]: return "بيع"
        return "محايد"


class ForceIndexIndicator(BaseIndicator):
    """#49 — Force Index"""
    id = 49
    name = "Force Index"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "C"
    min_bars = 25

    def _fi(self, df: pd.DataFrame, period: int = 13) -> pd.Series:
        if not _has_volume(df): return pd.Series([0.0] * len(df), index=df.index)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        return _ema(c.diff() * v, period)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._fi(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if not _has_volume(df): return "محايد"
        f = self._fi(df)
        if pd.isna(f.iloc[-1]): return "محايد"
        if f.iloc[-1] > 0 and f.iloc[-1] > f.iloc[-2]: return "شراء"
        if f.iloc[-1] < 0 and f.iloc[-1] < f.iloc[-2]: return "بيع"
        return "محايد"


class NVIIndicator(BaseIndicator):
    """#50 — Negative Volume Index"""
    id = 50
    name = "NVI - Negative Volume Index"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "C"
    min_bars = 25

    def _nvi(self, df: pd.DataFrame) -> pd.Series:
        if not _has_volume(df): return pd.Series([1000.0] * len(df), index=df.index)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        nvi = pd.Series(index=c.index, dtype=float)
        nvi.iloc[0] = 1000
        for i in range(1, len(c)):
            if v.iloc[i] < v.iloc[i - 1]:
                nvi.iloc[i] = nvi.iloc[i - 1] * (1 + (c.iloc[i] - c.iloc[i - 1]) / c.iloc[i - 1])
            else:
                nvi.iloc[i] = nvi.iloc[i - 1]
        return nvi

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._nvi(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if not _has_volume(df): return "محايد"
        nvi = self._nvi(df)
        if pd.isna(nvi.iloc[-1]) or len(nvi) < 256: return "محايد"
        ema_nvi = _ema(nvi, 255)
        if nvi.iloc[-1] > ema_nvi.iloc[-1]: return "شراء"
        return "محايد"


class PVIIndicator(BaseIndicator):
    """#51 — Positive Volume Index"""
    id = 51
    name = "PVI - Positive Volume Index"
    category = "مؤشرات الحجم"
    category_en = "Volume"
    tier = "C"
    min_bars = 25

    def _pvi(self, df: pd.DataFrame) -> pd.Series:
        if not _has_volume(df): return pd.Series([1000.0] * len(df), index=df.index)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        pvi = pd.Series(index=c.index, dtype=float)
        pvi.iloc[0] = 1000
        for i in range(1, len(c)):
            if v.iloc[i] > v.iloc[i - 1]:
                pvi.iloc[i] = pvi.iloc[i - 1] * (1 + (c.iloc[i] - c.iloc[i - 1]) / c.iloc[i - 1])
            else:
                pvi.iloc[i] = pvi.iloc[i - 1]
        return pvi

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._pvi(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if not _has_volume(df): return "محايد"
        pvi = self._pvi(df)
        if pd.isna(pvi.iloc[-1]) or len(pvi) < 256: return "محايد"
        ema_pvi = _ema(pvi, 255)
        if pvi.iloc[-1] > ema_pvi.iloc[-1]: return "شراء"
        return "محايد"
