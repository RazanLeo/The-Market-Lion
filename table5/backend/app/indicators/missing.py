# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشرات المفقودة — لإكمال الـ 71 حسب الإكسيل بالضبط
# تنفيذات لمؤشرات: McGinley, Linear Regression, Volatility Stop, FRAMA,
# Volatility Index, Chaikin Osc, Klinger Osc, Volume Osc, PVI/NVI, Anchored VWAP,
# VWAP Bands, Volume Profile POC/HVN/LVN, Market Profile TPO, Cumulative Delta,
# Fib Fan/Arcs/Time Zones/SpeedFan, %B+Bandwidth, McClellan, Arms TRIN, A/D Line
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator


def _ema(s: pd.Series, p: int) -> pd.Series:
    return s.ewm(span=p, adjust=False).mean()


def _atr(df: pd.DataFrame, p: int = 14) -> pd.Series:
    h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
    tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/p, adjust=False).mean()


# ─── Trend Extras ──────────────────────────────────────────────────────────
class McGinleyIndicator(BaseIndicator):
    """#10 — McGinley Dynamic"""
    id = 10; name = "McGinley Dynamic"; category = "مؤشرات الاتجاه"; category_en = "Trend"
    tier = "B"; min_bars = 30

    def _mg(self, c: pd.Series, p: int = 14) -> pd.Series:
        mg = pd.Series(index=c.index, dtype=float)
        mg.iloc[0] = c.iloc[0]
        for i in range(1, len(c)):
            prev = mg.iloc[i - 1]
            ratio = c.iloc[i] / prev if prev else 1.0
            mg.iloc[i] = prev + (c.iloc[i] - prev) / (p * (ratio ** 4))
        return mg

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float); v = self._mg(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float); m = self._mg(c)
        if pd.isna(m.iloc[-1]): return "محايد"
        last_c, last_m = c.iloc[-1], m.iloc[-1]
        if last_c > last_m and m.iloc[-1] > m.iloc[-3]: return "شراء"
        if last_c < last_m and m.iloc[-1] < m.iloc[-3]: return "بيع"
        return "محايد"


class LinearRegressionIndicator(BaseIndicator):
    """#11 — Linear Regression Slope/Channel"""
    id = 11; name = "Linear Regression"; category = "مؤشرات الاتجاه"; category_en = "Trend"
    tier = "B"; min_bars = 30

    def _slope(self, c: pd.Series, p: int = 14) -> pd.Series:
        x = np.arange(p)
        return c.rolling(p).apply(lambda y: np.polyfit(x, y, 1)[0], raw=True)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float); v = self._slope(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float); s = self._slope(c)
        if pd.isna(s.iloc[-1]): return "محايد"
        if s.iloc[-1] > 0 and s.iloc[-1] > s.iloc[-3]: return "شراء"
        if s.iloc[-1] < 0 and s.iloc[-1] < s.iloc[-3]: return "بيع"
        return "محايد"


class VolatilityStopIndicator(BaseIndicator):
    """#12 — Volatility Stop (ATR Trailing Stop)"""
    id = 12; name = "Volatility Stop"; category = "مؤشرات الاتجاه"; category_en = "Trend"
    tier = "B"; min_bars = 30

    def _vstop(self, df: pd.DataFrame, period: int = 20, mult: float = 2.0) -> pd.Series:
        c = df["close"].astype(float); a = _atr(df, period)
        stop = pd.Series(index=c.index, dtype=float)
        long = True; stop.iloc[0] = c.iloc[0] - mult * a.iloc[0]
        for i in range(1, len(c)):
            if long:
                stop.iloc[i] = max(stop.iloc[i - 1], c.iloc[i] - mult * a.iloc[i])
                if c.iloc[i] < stop.iloc[i]: long = False; stop.iloc[i] = c.iloc[i] + mult * a.iloc[i]
            else:
                stop.iloc[i] = min(stop.iloc[i - 1], c.iloc[i] + mult * a.iloc[i])
                if c.iloc[i] > stop.iloc[i]: long = True; stop.iloc[i] = c.iloc[i] - mult * a.iloc[i]
        return stop

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._vstop(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float); s = self._vstop(df)
        if pd.isna(s.iloc[-1]): return "محايد"
        return "شراء" if c.iloc[-1] > s.iloc[-1] else "بيع"


# ─── Volatility Extras ─────────────────────────────────────────────────────
class FRAMAIndicator(BaseIndicator):
    """#32 — Fractal Adaptive MA"""
    id = 32; name = "FRAMA"; category = "مؤشرات التذبذب والتقلب"; category_en = "Volatility"
    tier = "B"; min_bars = 30

    def _frama(self, df: pd.DataFrame, period: int = 16) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        n = period; half = n // 2
        result = pd.Series(index=c.index, dtype=float)
        for i in range(n, len(c)):
            h1 = h.iloc[i - n + 1: i - half + 1].max()
            l1 = l.iloc[i - n + 1: i - half + 1].min()
            h2 = h.iloc[i - half + 1: i + 1].max()
            l2 = l.iloc[i - half + 1: i + 1].min()
            h3 = h.iloc[i - n + 1: i + 1].max()
            l3 = l.iloc[i - n + 1: i + 1].min()
            n1 = (h1 - l1) / half if half else 1
            n2 = (h2 - l2) / half if half else 1
            n3 = (h3 - l3) / n if n else 1
            if n1 + n2 > 0 and n3 > 0:
                d = (np.log(n1 + n2) - np.log(n3)) / np.log(2)
            else:
                d = 1
            alpha = max(0.01, min(np.exp(-4.6 * (d - 1)), 1.0))
            prev = result.iloc[i - 1] if pd.notna(result.iloc[i - 1]) else c.iloc[i - 1]
            result.iloc[i] = alpha * c.iloc[i] + (1 - alpha) * prev
        return result

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._frama(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float); f = self._frama(df)
        if pd.isna(f.iloc[-1]): return "محايد"
        if c.iloc[-1] > f.iloc[-1] and f.iloc[-1] > f.iloc[-3]: return "شراء"
        if c.iloc[-1] < f.iloc[-1] and f.iloc[-1] < f.iloc[-3]: return "بيع"
        return "محايد"


class VolatilityIndexIndicator(BaseIndicator):
    """#39 — Volatility Index (VIX-like)"""
    id = 39; name = "Volatility Index"; category = "مؤشرات التذبذب والتقلب"; category_en = "Volatility"
    tier = "C"; min_bars = 25

    def _vi(self, df: pd.DataFrame) -> pd.Series:
        c = df["close"].astype(float)
        return _atr(df, 14) / c * 100

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._vi(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float); vi = self._vi(df)
        if pd.isna(vi.iloc[-1]) or len(vi) < 30: return "محايد"
        avg = vi.iloc[-30:].mean()
        if vi.iloc[-1] > avg * 1.5 and c.iloc[-1] < c.iloc[-5]: return "شراء"  # خوف = انعكاس قاع
        if vi.iloc[-1] < avg * 0.5 and c.iloc[-1] > c.iloc[-5]: return "بيع"   # رضى = انعكاس قمة
        return "محايد"


# ─── Volume Extras ─────────────────────────────────────────────────────────
class ChaikinOscIndicator(BaseIndicator):
    """#45 — Chaikin Oscillator"""
    id = 45; name = "Chaikin Oscillator"; category = "مؤشرات الحجم والتدفق"; category_en = "Volume"
    tier = "B"; min_bars = 30

    def _co(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return pd.Series([0.0] * len(df), index=df.index)
        h = df["high"].astype(float); l = df["low"].astype(float)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        clv = ((c - l) - (h - c)) / (h - l).replace(0, np.nan)
        ad = (clv * v).cumsum()
        return _ema(ad, 3) - _ema(ad, 10)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._co(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        co = self._co(df)
        if pd.isna(co.iloc[-1]): return "محايد"
        if co.iloc[-1] > 0 and co.iloc[-2] <= 0: return "شراء"
        if co.iloc[-1] < 0 and co.iloc[-2] >= 0: return "بيع"
        return "محايد"


class KlingerOscIndicator(BaseIndicator):
    """#46 — Klinger Oscillator"""
    id = 46; name = "Klinger Oscillator"; category = "مؤشرات الحجم والتدفق"; category_en = "Volume"
    tier = "B"; min_bars = 60

    def _kvo(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return pd.Series([0.0] * len(df), index=df.index)
        h = df["high"].astype(float); l = df["low"].astype(float)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        hlc = (h + l + c) / 3.0
        sign = np.sign(hlc.diff().fillna(0))
        kv = sign * v
        return _ema(kv, 34) - _ema(kv, 55)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._kvo(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        k = self._kvo(df)
        if pd.isna(k.iloc[-1]): return "محايد"
        if k.iloc[-1] > 0 and k.iloc[-2] <= 0: return "شراء"
        if k.iloc[-1] < 0 and k.iloc[-2] >= 0: return "بيع"
        return "محايد"


class VolumeOscIndicator(BaseIndicator):
    """#49 — Volume Oscillator"""
    id = 49; name = "Volume Oscillator"; category = "مؤشرات الحجم والتدفق"; category_en = "Volume"
    tier = "C"; min_bars = 30

    def _vo(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return pd.Series([0.0] * len(df), index=df.index)
        v = df["volume"].astype(float)
        short = v.rolling(5).mean(); long = v.rolling(20).mean()
        return (short - long) / long.replace(0, np.nan) * 100

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._vo(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float); vo = self._vo(df)
        if pd.isna(vo.iloc[-1]): return "محايد"
        # حجم متزايد + سعر صاعد = شراء
        if vo.iloc[-1] > 0 and c.iloc[-1] > c.iloc[-3]: return "شراء"
        if vo.iloc[-1] > 0 and c.iloc[-1] < c.iloc[-3]: return "بيع"
        return "محايد"


class PVIIndexIndicator(BaseIndicator):
    """#50 — Positive/Negative Volume Index combined"""
    id = 50; name = "Positive / Negative Volume Index"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "C"; min_bars = 100

    def _pvi_nvi(self, df: pd.DataFrame):
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return None, None
        c = df["close"].astype(float); v = df["volume"].astype(float)
        pvi = pd.Series([1000.0] * len(c), index=c.index)
        nvi = pd.Series([1000.0] * len(c), index=c.index)
        for i in range(1, len(c)):
            ret = (c.iloc[i] - c.iloc[i - 1]) / c.iloc[i - 1] if c.iloc[i - 1] else 0
            if v.iloc[i] > v.iloc[i - 1]:
                pvi.iloc[i] = pvi.iloc[i - 1] * (1 + ret); nvi.iloc[i] = nvi.iloc[i - 1]
            elif v.iloc[i] < v.iloc[i - 1]:
                nvi.iloc[i] = nvi.iloc[i - 1] * (1 + ret); pvi.iloc[i] = pvi.iloc[i - 1]
            else:
                pvi.iloc[i] = pvi.iloc[i - 1]; nvi.iloc[i] = nvi.iloc[i - 1]
        return pvi, nvi

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        p, n = self._pvi_nvi(df)
        if p is None: return None
        return float(p.iloc[-1] - n.iloc[-1])

    def compute_signal(self, df: pd.DataFrame) -> str:
        p, n = self._pvi_nvi(df)
        if p is None or len(p) < 100: return "محايد"
        # PVI أعلى من EMA(255) = ضغط شراء بحجم متزايد
        if p.iloc[-1] > _ema(p, 100).iloc[-1] and n.iloc[-1] > _ema(n, 100).iloc[-1]: return "شراء"
        if p.iloc[-1] < _ema(p, 100).iloc[-1] and n.iloc[-1] < _ema(n, 100).iloc[-1]: return "بيع"
        return "محايد"


class NegativeVolIndex51(BaseIndicator):
    """#51 — Negative Volume Index (standalone)"""
    id = 51; name = "Negative Volume Index"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "C"; min_bars = 100

    def _nvi(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return pd.Series([1000.0] * len(df), index=df.index)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        nvi = pd.Series([1000.0] * len(c), index=c.index)
        for i in range(1, len(c)):
            if v.iloc[i] < v.iloc[i - 1]:
                ret = (c.iloc[i] - c.iloc[i - 1]) / c.iloc[i - 1] if c.iloc[i - 1] else 0
                nvi.iloc[i] = nvi.iloc[i - 1] * (1 + ret)
            else:
                nvi.iloc[i] = nvi.iloc[i - 1]
        return nvi

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._nvi(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        nvi = self._nvi(df)
        if len(nvi) < 100: return "محايد"
        ema_nvi = _ema(nvi, 100)
        if nvi.iloc[-1] > ema_nvi.iloc[-1]: return "شراء"
        return "محايد"


# ─── VWAP / Volume Profile / Market Profile ────────────────────────────────
class VWAPBasicIndicator(BaseIndicator):
    """#52 — VWAP (الأساسي)"""
    id = 52; name = "VWAP (الأساسي)"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "S"; min_bars = 20

    def _vwap(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return df["close"].astype(float).rolling(20).mean()
        h = df["high"].astype(float); l = df["low"].astype(float)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        tp = (h + l + c) / 3.0
        return (tp * v).cumsum() / v.cumsum().replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._vwap(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float); vw = self._vwap(df)
        if pd.isna(vw.iloc[-1]): return "محايد"
        if c.iloc[-1] > vw.iloc[-1] and c.iloc[-2] <= vw.iloc[-2]: return "شراء"
        if c.iloc[-1] < vw.iloc[-1] and c.iloc[-2] >= vw.iloc[-2]: return "بيع"
        if c.iloc[-1] > vw.iloc[-1] * 1.005: return "شراء"
        if c.iloc[-1] < vw.iloc[-1] * 0.995: return "بيع"
        return "محايد"


class AnchoredVWAPIndicator(BaseIndicator):
    """#53 — Anchored VWAP (من أعلى نقطة في 50 شمعة)"""
    id = 53; name = "Anchored VWAP"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "A"; min_bars = 50

    def _avwap(self, df: pd.DataFrame, lookback: int = 50) -> float:
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return float(df["close"].iloc[-1])
        recent = df.iloc[-lookback:]
        anchor_idx = recent["high"].astype(float).idxmax()
        from_anchor = df.loc[anchor_idx:]
        h = from_anchor["high"].astype(float); l = from_anchor["low"].astype(float)
        c = from_anchor["close"].astype(float); v = from_anchor["volume"].astype(float)
        tp = (h + l + c) / 3.0
        cum_pv = (tp * v).sum(); cum_v = v.sum()
        return float(cum_pv / cum_v) if cum_v else float(c.iloc[-1])

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        return self._avwap(df) if len(df) >= 50 else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 50: return "محايد"
        avwap = self._avwap(df)
        c = float(df["close"].iloc[-1])
        if c > avwap * 1.003: return "شراء"
        if c < avwap * 0.997: return "بيع"
        return "محايد"


class VolumeProfileVPVRIndicator(BaseIndicator):
    """#54 — Volume Profile (VPVR / VPSR)"""
    id = 54; name = "Volume Profile (VPVR / VPSR)"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "S"; min_bars = 50

    def _poc(self, df: pd.DataFrame, bins: int = 30):
        if len(df) < 30: return None, None, None
        c = df["close"].astype(float).values
        v = (df["volume"].astype(float).values
             if "volume" in df.columns and df["volume"].sum() > 0
             else np.ones_like(c))
        hist, edges = np.histogram(c, bins=bins, weights=v)
        if hist.sum() == 0: return None, None, None
        idx = int(np.argmax(hist))
        poc = float((edges[idx] + edges[idx + 1]) / 2.0)
        # VAH/VAL from 70% volume
        target = hist.sum() * 0.70; acc = hist[idx]; lo, hi = idx, idx
        while acc < target and (lo > 0 or hi < len(hist) - 1):
            left = hist[lo - 1] if lo > 0 else -1
            right = hist[hi + 1] if hi < len(hist) - 1 else -1
            if right >= left: hi += 1; acc += hist[hi]
            else: lo -= 1; acc += hist[lo]
        return poc, float(edges[hi + 1]), float(edges[lo])

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        poc, _, _ = self._poc(df); return poc

    def compute_signal(self, df: pd.DataFrame) -> str:
        poc, vah, val = self._poc(df)
        if poc is None: return "محايد"
        c = float(df["close"].iloc[-1])
        if c < val: return "شراء"
        if c > vah: return "بيع"
        return "محايد"


class VWAPBandsIndicator(BaseIndicator):
    """#55 — VWAP with Standard Deviation Bands"""
    id = 55; name = "VWAP with Standard Deviation Bands"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "S"; min_bars = 30

    def _vwap_bands(self, df: pd.DataFrame, mult: float = 2.0):
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return None
        h = df["high"].astype(float); l = df["low"].astype(float)
        c = df["close"].astype(float); v = df["volume"].astype(float)
        tp = (h + l + c) / 3.0
        cum_v = v.cumsum().replace(0, np.nan)
        vwap = (tp * v).cumsum() / cum_v
        var = ((tp - vwap) ** 2 * v).cumsum() / cum_v
        std = np.sqrt(var)
        return vwap, vwap + mult * std, vwap - mult * std

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        bands = self._vwap_bands(df)
        if bands is None: return None
        return float(bands[0].iloc[-1])

    def compute_signal(self, df: pd.DataFrame) -> str:
        bands = self._vwap_bands(df)
        if bands is None: return "محايد"
        vwap, upper, lower = bands
        c = float(df["close"].iloc[-1])
        if c < lower.iloc[-1]: return "شراء"
        if c > upper.iloc[-1]: return "بيع"
        return "محايد"


class VolumeProfilePOCIndicator(BaseIndicator):
    """#56 — Volume Profile with POC / HVN / LVN"""
    id = 56; name = "Volume Profile with POC / HVN / LVN"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "S"; min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        if len(df) < 30: return None
        c = df["close"].astype(float).values
        v = (df["volume"].astype(float).values
             if "volume" in df.columns and df["volume"].sum() > 0
             else np.ones_like(c))
        hist, edges = np.histogram(c, bins=30, weights=v)
        if hist.sum() == 0: return None
        return float((edges[int(np.argmax(hist))] + edges[int(np.argmax(hist)) + 1]) / 2.0)

    def compute_signal(self, df: pd.DataFrame) -> str:
        poc = self.compute_raw_value(df)
        if poc is None: return "محايد"
        c = float(df["close"].iloc[-1])
        # ارتداد من POC = اتجاه السعر
        if abs(c - poc) / poc < 0.003:
            # السعر عند POC — انتظر اختراق
            return "محايد"
        if c > poc * 1.005: return "شراء"  # كسر فوق
        if c < poc * 0.995: return "بيع"
        return "محايد"


class MarketProfileTPOIndicator(BaseIndicator):
    """#57 — Market Profile (TPO) — تنفيذ مبسّط"""
    id = 57; name = "Market Profile (TPO)"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "S"; min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        # TPO POC = أكثر سعر تمت زيارته
        if len(df) < 30: return None
        c = df["close"].astype(float).values
        hist, edges = np.histogram(c, bins=30)
        return float((edges[int(np.argmax(hist))] + edges[int(np.argmax(hist)) + 1]) / 2.0)

    def compute_signal(self, df: pd.DataFrame) -> str:
        tpo_poc = self.compute_raw_value(df)
        if tpo_poc is None: return "محايد"
        c = float(df["close"].iloc[-1])
        if c > tpo_poc * 1.005: return "شراء"
        if c < tpo_poc * 0.995: return "بيع"
        return "محايد"


class CumulativeDeltaIndicator(BaseIndicator):
    """#58 — Cumulative Delta (Buy − Sell)"""
    id = 58; name = "Cumulative Delta"; category = "مؤشرات الحجم والتدفق"
    category_en = "Volume"; tier = "S"; min_bars = 30

    def _cdelta(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns or df["volume"].sum() == 0:
            return pd.Series([0.0] * len(df), index=df.index)
        c = df["close"].astype(float); o = df["open"].astype(float); v = df["volume"].astype(float)
        # تقريب: الشمعة الصاعدة volumen كله شراء، الهابطة كله بيع
        delta = np.where(c > o, v, np.where(c < o, -v, 0))
        return pd.Series(delta, index=c.index).cumsum()

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._cdelta(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        cd = self._cdelta(df)
        c = df["close"].astype(float)
        if pd.isna(cd.iloc[-1]) or len(cd) < 11: return "محايد"
        cd_up = cd.iloc[-1] > cd.iloc[-10]
        price_up = c.iloc[-1] > c.iloc[-10]
        if cd_up and price_up: return "شراء"
        if not cd_up and not price_up: return "بيع"
        # Divergence
        if cd_up and not price_up: return "شراء"  # bullish divergence
        if not cd_up and price_up: return "بيع"   # bearish divergence
        return "محايد"


# ─── Fibonacci Family ───────────────────────────────────────────────────────
def _swing_range(df: pd.DataFrame, lookback: int = 50):
    if len(df) < lookback: return None, None
    h = df["high"].astype(float).iloc[-lookback:].max()
    l = df["low"].astype(float).iloc[-lookback:].min()
    return float(h), float(l)


class FibFanIndicator(BaseIndicator):
    """#63 — Fibonacci Fan"""
    id = 63; name = "Fibonacci Fan"; category = "الدعم والمقاومة وفيبوناتشي"
    category_en = "Support/Resistance"; tier = "B"; min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float: return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        h, l = _swing_range(df, 50)
        if h is None or h == l: return "محايد"
        c = float(df["close"].iloc[-1])
        ratio = (c - l) / (h - l)
        # خطوط مروحة فيبو عند 0.382 و 0.618
        if 0.36 < ratio < 0.40: return "شراء"
        if 0.60 < ratio < 0.64: return "بيع"
        return "محايد"


class FibArcsIndicator(BaseIndicator):
    """#64 — Fibonacci Arcs"""
    id = 64; name = "Fibonacci Arcs"; category = "الدعم والمقاومة وفيبوناتشي"
    category_en = "Support/Resistance"; tier = "C"; min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float: return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        h, l = _swing_range(df, 50)
        if h is None or h == l: return "محايد"
        c = float(df["close"].iloc[-1])
        ratio = (c - l) / (h - l)
        # أقواس عند 0.382/0.5/0.618 — إشارات أضعف
        if ratio < 0.382: return "شراء"
        if ratio > 0.618: return "بيع"
        return "محايد"


class FibTimeZonesIndicator(BaseIndicator):
    """#65 — Fibonacci Time Zones"""
    id = 65; name = "Fibonacci Time Zones"; category = "الدعم والمقاومة وفيبوناتشي"
    category_en = "Support/Resistance"; tier = "C"; min_bars = 30

    def compute_raw_value(self, df: pd.DataFrame) -> float: return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        # TimeZones = شموع عند 8، 13، 21 من القاع
        if len(df) < 30: return "محايد"
        l = df["low"].astype(float)
        anchor = int(l.iloc[-30:].idxmin()) if hasattr(l.iloc[-30:].idxmin(), '__int__') else None
        if anchor is None: return "محايد"
        bars_since = len(df) - 1 - anchor
        # إشارة عند فيبو time zones
        if bars_since in (8, 13, 21):
            c = df["close"].astype(float)
            if c.iloc[-1] > c.iloc[-2]: return "شراء"
            if c.iloc[-1] < c.iloc[-2]: return "بيع"
        return "محايد"


class FibSpeedFanIndicator(BaseIndicator):
    """#66 — Fibonacci Speed Resistance Fan"""
    id = 66; name = "Fibonacci Speed Resistance Fan"; category = "الدعم والمقاومة وفيبوناتشي"
    category_en = "Support/Resistance"; tier = "C"; min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float: return None

    def compute_signal(self, df: pd.DataFrame) -> str:
        h, l = _swing_range(df, 50)
        if h is None or h == l: return "محايد"
        c = float(df["close"].iloc[-1])
        ratio = (c - l) / (h - l)
        if ratio < 0.236: return "شراء"
        if ratio > 0.764: return "بيع"
        return "محايد"


# ─── Integrated / Breadth ─────────────────────────────────────────────────
class BollingerBPercentBandwidthIndicator(BaseIndicator):
    """#68 — Bollinger %B + Bandwidth"""
    id = 68; name = "Bollinger %B + Bandwidth"; category = "مؤشرات متكاملة"
    category_en = "Integrated"; tier = "A"; min_bars = 25

    def _calc(self, df: pd.DataFrame, period: int = 20, mult: float = 2.0):
        c = df["close"].astype(float)
        mid = c.rolling(period).mean(); std = c.rolling(period).std(ddof=0)
        upper = mid + mult * std; lower = mid - mult * std
        pct_b = (c - lower) / (upper - lower).replace(0, np.nan)
        bw = (upper - lower) / mid.replace(0, np.nan)
        return pct_b, bw

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        pct_b, _ = self._calc(df)
        v = pct_b.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        pct_b, bw = self._calc(df)
        if pd.isna(pct_b.iloc[-1]) or pd.isna(bw.iloc[-1]): return "محايد"
        # Squeeze (BW منخفض) + اختراق = إشارة قوية
        if len(bw) >= 22:
            squeeze = bw.iloc[-1] < bw.iloc[-22:].mean() * 0.8
            if squeeze and pct_b.iloc[-1] > 0.8: return "شراء"
            if squeeze and pct_b.iloc[-1] < 0.2: return "بيع"
        if pct_b.iloc[-1] < 0: return "شراء"
        if pct_b.iloc[-1] > 1: return "بيع"
        return "محايد"


class McClellanOscIndicator(BaseIndicator):
    """#69 — McClellan Oscillator (تقريب من breadth داخلي)"""
    id = 69; name = "McClellan Oscillator"; category = "مؤشرات متكاملة"
    category_en = "Integrated"; tier = "C"; min_bars = 50

    def _mclellan(self, df: pd.DataFrame) -> pd.Series:
        # تقريب: نستخدم advance/decline من السعر (1 صعود، -1 هبوط)
        c = df["close"].astype(float)
        adv_dec = np.sign(c.diff().fillna(0))
        return _ema(adv_dec, 19) - _ema(adv_dec, 39)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._mclellan(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        m = self._mclellan(df)
        if pd.isna(m.iloc[-1]): return "محايد"
        if m.iloc[-1] > 0 and m.iloc[-1] > m.iloc[-2]: return "شراء"
        if m.iloc[-1] < 0 and m.iloc[-1] < m.iloc[-2]: return "بيع"
        return "محايد"


class ArmsTRINIndicator(BaseIndicator):
    """#70 — Arms Index (TRIN)"""
    id = 70; name = "Arms Index (TRIN)"; category = "مؤشرات متكاملة"
    category_en = "Integrated"; tier = "C"; min_bars = 30

    def _trin(self, df: pd.DataFrame) -> pd.Series:
        # تقريب: TRIN = (advances/declines) / (volume_up/volume_down)
        c = df["close"].astype(float)
        v = (df["volume"].astype(float)
             if "volume" in df.columns and df["volume"].sum() > 0
             else pd.Series([1.0] * len(c), index=c.index))
        ret = c.diff()
        adv = (ret > 0).rolling(10).sum()
        dec = (ret < 0).rolling(10).sum()
        vol_up = v.where(ret > 0, 0).rolling(10).sum()
        vol_dn = v.where(ret < 0, 0).rolling(10).sum()
        return (adv / dec.replace(0, np.nan)) / (vol_up / vol_dn.replace(0, np.nan)).replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._trin(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        t = self._trin(df)
        if pd.isna(t.iloc[-1]): return "محايد"
        if t.iloc[-1] < 0.8: return "شراء"
        if t.iloc[-1] > 1.2: return "بيع"
        return "محايد"


class AdvanceDeclineLineIndicator(BaseIndicator):
    """#71 — Advance / Decline Line"""
    id = 71; name = "Advance / Decline Line"; category = "مؤشرات متكاملة"
    category_en = "Integrated"; tier = "C"; min_bars = 30

    def _adl(self, df: pd.DataFrame) -> pd.Series:
        c = df["close"].astype(float)
        net = np.sign(c.diff().fillna(0))
        return net.cumsum()

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._adl(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        adl = self._adl(df)
        c = df["close"].astype(float)
        if len(adl) < 11 or pd.isna(adl.iloc[-1]): return "محايد"
        adl_up = adl.iloc[-1] > adl.iloc[-10]
        price_up = c.iloc[-1] > c.iloc[-10]
        if adl_up and price_up: return "شراء"
        if not adl_up and not price_up: return "بيع"
        return "محايد"
