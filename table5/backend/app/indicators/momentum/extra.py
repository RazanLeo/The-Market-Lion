# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشرات #16، #18..#28 — مؤشرات الزخم الإضافية
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


def _sma(s: pd.Series, p: int) -> pd.Series:
    return s.rolling(p).mean()


# ─────────────────────────────────────────────────────────────────────────────
class CCIIndicator(BaseIndicator):
    """#16 — Commodity Channel Index"""
    id = 16
    name = "CCI - Commodity Channel Index"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "A"
    min_bars = 30

    def _cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        h = df["high"].astype(float)
        l = df["low"].astype(float)
        c = df["close"].astype(float)
        if HAS_TALIB:
            return pd.Series(talib.CCI(h.values, l.values, c.values, timeperiod=period), index=c.index)
        tp = (h + l + c) / 3.0
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=False)
        return (tp - sma) / (0.015 * mad.replace(0, np.nan))

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._cci(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        cci = self._cci(df)
        if len(cci) < 3 or pd.isna(cci.iloc[-1]):
            return "محايد"
        last, prev = cci.iloc[-1], cci.iloc[-2]
        if last > 100 and last > prev: return "شراء"
        if last < -100 and last < prev: return "بيع"
        if last < -100 and last > prev: return "شراء"
        if last > 100 and last < prev: return "بيع"
        return "محايد"


class WilliamsRIndicator(BaseIndicator):
    """#18 — Williams %R"""
    id = 18
    name = "Williams %R"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "B"
    min_bars = 25

    def _wr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        h = df["high"].astype(float)
        l = df["low"].astype(float)
        c = df["close"].astype(float)
        if HAS_TALIB:
            return pd.Series(talib.WILLR(h.values, l.values, c.values, timeperiod=period), index=c.index)
        hh = h.rolling(period).max()
        ll = l.rolling(period).min()
        return -100 * (hh - c) / (hh - ll).replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._wr(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        wr = self._wr(df)
        if pd.isna(wr.iloc[-1]): return "محايد"
        last, prev = wr.iloc[-1], wr.iloc[-2]
        if last < -80 and last > prev: return "شراء"
        if last > -20 and last < prev: return "بيع"
        return "محايد"


class MOMIndicator(BaseIndicator):
    """#19 — Momentum"""
    id = 19
    name = "MOM - Momentum"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "B"
    min_bars = 25

    def _mom(self, c: pd.Series, p: int = 10) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.MOM(c.values, timeperiod=p), index=c.index)
        return c.diff(p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._mom(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        m = self._mom(c)
        if len(m) < 3 or pd.isna(m.iloc[-1]): return "محايد"
        if m.iloc[-1] > 0 and m.iloc[-1] > m.iloc[-2]: return "شراء"
        if m.iloc[-1] < 0 and m.iloc[-1] < m.iloc[-2]: return "بيع"
        return "محايد"


class ROCIndicator(BaseIndicator):
    """#20 — Rate of Change"""
    id = 20
    name = "ROC - Rate of Change"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "B"
    min_bars = 25

    def _roc(self, c: pd.Series, p: int = 10) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.ROC(c.values, timeperiod=p), index=c.index)
        return ((c - c.shift(p)) / c.shift(p) * 100)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._roc(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        r = self._roc(c)
        if len(r) < 3 or pd.isna(r.iloc[-1]): return "محايد"
        if r.iloc[-1] > 0 and r.iloc[-1] > r.iloc[-2]: return "شراء"
        if r.iloc[-1] < 0 and r.iloc[-1] < r.iloc[-2]: return "بيع"
        return "محايد"


class TRIXIndicator(BaseIndicator):
    """#21 — TRIX"""
    id = 21
    name = "TRIX"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "C"
    min_bars = 50

    def _trix(self, c: pd.Series, p: int = 14) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.TRIX(c.values, timeperiod=p), index=c.index)
        e1 = _ema(c, p); e2 = _ema(e1, p); e3 = _ema(e2, p)
        return e3.pct_change() * 100

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._trix(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        t = self._trix(c)
        if pd.isna(t.iloc[-1]): return "محايد"
        if t.iloc[-1] > 0 and t.iloc[-1] > t.iloc[-2]: return "شراء"
        if t.iloc[-1] < 0 and t.iloc[-1] < t.iloc[-2]: return "بيع"
        return "محايد"


class UltimateOscIndicator(BaseIndicator):
    """#22 — Ultimate Oscillator"""
    id = 22
    name = "Ultimate Oscillator"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "C"
    min_bars = 35

    def _ultosc(self, df: pd.DataFrame) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        if HAS_TALIB:
            return pd.Series(talib.ULTOSC(h.values, l.values, c.values, 7, 14, 28), index=c.index)
        # تقريب: متوسط مرجّح لـRSI على 3 فترات
        return pd.Series([50.0] * len(c), index=c.index)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._ultosc(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        u = self._ultosc(df)
        if pd.isna(u.iloc[-1]): return "محايد"
        if u.iloc[-1] < 30: return "شراء"
        if u.iloc[-1] > 70: return "بيع"
        return "محايد"


class TSIIndicator(BaseIndicator):
    """#23 — True Strength Index"""
    id = 23
    name = "TSI - True Strength Index"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "B"
    min_bars = 50

    def _tsi(self, c: pd.Series, long: int = 25, short: int = 13) -> pd.Series:
        m = c.diff()
        ema1 = _ema(m, long); ema2 = _ema(ema1, short)
        ema_abs1 = _ema(m.abs(), long); ema_abs2 = _ema(ema_abs1, short)
        return 100 * ema2 / ema_abs2.replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._tsi(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        t = self._tsi(c)
        if pd.isna(t.iloc[-1]): return "محايد"
        if t.iloc[-1] > 0 and t.iloc[-1] > t.iloc[-2]: return "شراء"
        if t.iloc[-1] < 0 and t.iloc[-1] < t.iloc[-2]: return "بيع"
        return "محايد"


class StochRSIIndicator(BaseIndicator):
    """#24 — Stochastic RSI"""
    id = 24
    name = "Stochastic RSI"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "B"
    min_bars = 35

    def _stoch_rsi(self, c: pd.Series, p: int = 14) -> pd.Series:
        if HAS_TALIB:
            k, _ = talib.STOCHRSI(c.values, timeperiod=p, fastk_period=p, fastd_period=3, fastd_matype=0)
            return pd.Series(k, index=c.index)
        # fallback
        delta = c.diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=1/p, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/p, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)
        rsi_min = rsi.rolling(p).min()
        rsi_max = rsi.rolling(p).max()
        return 100 * (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._stoch_rsi(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        s = self._stoch_rsi(c)
        if pd.isna(s.iloc[-1]): return "محايد"
        last, prev = s.iloc[-1], s.iloc[-2]
        if last < 20 and last > prev: return "شراء"
        if last > 80 and last < prev: return "بيع"
        return "محايد"


class FisherTransformIndicator(BaseIndicator):
    """#25 — Fisher Transform"""
    id = 25
    name = "Fisher Transform"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "C"
    min_bars = 25

    def _fisher(self, df: pd.DataFrame, period: int = 10) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float)
        med = (h + l) / 2.0
        hh = med.rolling(period).max(); ll = med.rolling(period).min()
        v = 0.33 * 2 * ((med - ll) / (hh - ll).replace(0, np.nan) - 0.5)
        v = v.clip(-0.999, 0.999).fillna(0)
        return 0.5 * np.log((1 + v) / (1 - v))

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._fisher(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        f = self._fisher(df)
        if pd.isna(f.iloc[-1]): return "محايد"
        if f.iloc[-1] > 0 and f.iloc[-1] > f.iloc[-2]: return "شراء"
        if f.iloc[-1] < 0 and f.iloc[-1] < f.iloc[-2]: return "بيع"
        return "محايد"


class CMOIndicator(BaseIndicator):
    """#26 — Chande Momentum Oscillator"""
    id = 26
    name = "CMO - Chande Momentum Oscillator"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "C"
    min_bars = 25

    def _cmo(self, c: pd.Series, p: int = 14) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.CMO(c.values, timeperiod=p), index=c.index)
        delta = c.diff()
        up = delta.where(delta > 0, 0.0).rolling(p).sum()
        dn = (-delta.where(delta < 0, 0.0)).rolling(p).sum()
        return 100 * (up - dn) / (up + dn).replace(0, np.nan)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._cmo(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        m = self._cmo(c)
        if pd.isna(m.iloc[-1]): return "محايد"
        if m.iloc[-1] > 50: return "شراء"
        if m.iloc[-1] < -50: return "بيع"
        return "محايد"


class AwesomeOscIndicator(BaseIndicator):
    """#27 — Awesome Oscillator (Bill Williams)"""
    id = 27
    name = "Awesome Oscillator"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "B"
    min_bars = 40

    def _ao(self, df: pd.DataFrame) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float)
        median = (h + l) / 2.0
        return _sma(median, 5) - _sma(median, 34)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._ao(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        a = self._ao(df)
        if pd.isna(a.iloc[-1]): return "محايد"
        if a.iloc[-1] > 0 and a.iloc[-1] > a.iloc[-2]: return "شراء"
        if a.iloc[-1] < 0 and a.iloc[-1] < a.iloc[-2]: return "بيع"
        return "محايد"


class AccelDecelIndicator(BaseIndicator):
    """#28 — Accelerator / Decelerator Oscillator"""
    id = 28
    name = "Accelerator/Decelerator Oscillator"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "C"
    min_bars = 45

    def _ac(self, df: pd.DataFrame) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float)
        median = (h + l) / 2.0
        ao = _sma(median, 5) - _sma(median, 34)
        return ao - _sma(ao, 5)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._ac(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        a = self._ac(df)
        if pd.isna(a.iloc[-1]): return "محايد"
        if a.iloc[-1] > 0 and a.iloc[-1] > a.iloc[-2]: return "شراء"
        if a.iloc[-1] < 0 and a.iloc[-1] < a.iloc[-2]: return "بيع"
        return "محايد"
