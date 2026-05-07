# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشرات #1..#12 — مجموعة المتوسطات المتحركة (Trend)
# الاستراتيجية المشتركة: السعر فوق المتوسط = شراء، تحت = بيع
#                       تقاطع متوسطين قصير/طويل = إشارة قوية
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
    return s.rolling(window=p).mean()


def _wma(s: pd.Series, p: int) -> pd.Series:
    weights = np.arange(1, p + 1)
    return s.rolling(p).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def _hma(s: pd.Series, p: int) -> pd.Series:
    half = max(1, p // 2)
    sqrtp = max(1, int(np.sqrt(p)))
    return _wma(2 * _wma(s, half) - _wma(s, p), sqrtp)


def _dema(s: pd.Series, p: int) -> pd.Series:
    e1 = _ema(s, p)
    return 2 * e1 - _ema(e1, p)


def _tema(s: pd.Series, p: int) -> pd.Series:
    e1 = _ema(s, p)
    e2 = _ema(e1, p)
    e3 = _ema(e2, p)
    return 3 * (e1 - e2) + e3


def _trend_signal_from_ma(close: pd.Series, ma_short: pd.Series, ma_long: pd.Series) -> str:
    """إشارة عامة من تقاطع متوسطات + موقع السعر"""
    if len(ma_short) < 3 or pd.isna(ma_short.iloc[-1]) or pd.isna(ma_long.iloc[-1]):
        return "محايد"
    last_close = close.iloc[-1]
    s_now, s_prev = ma_short.iloc[-1], ma_short.iloc[-2]
    l_now, l_prev = ma_long.iloc[-1], ma_long.iloc[-2]

    # تقاطع ذهبي
    if s_prev <= l_prev and s_now > l_now and last_close > s_now:
        return "شراء"
    # تقاطع موت
    if s_prev >= l_prev and s_now < l_now and last_close < s_now:
        return "بيع"
    # موقع السعر فوق/تحت كلا المتوسطين
    if last_close > s_now > l_now:
        return "شراء"
    if last_close < s_now < l_now:
        return "بيع"
    return "محايد"


# ─────────────────────────────────────────────────────────────────────────────
class SMAIndicator(BaseIndicator):
    id = 1
    name = "SMA - Simple Moving Average"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "S"
    min_bars = 60

    def _ma(self, c: pd.Series, p: int) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.SMA(c.values, timeperiod=p), index=c.index)
        return _sma(c, p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        ma = self._ma(c, 20)
        v = ma.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, self._ma(c, 20), self._ma(c, 50))


class EMAIndicator(BaseIndicator):
    id = 2
    name = "EMA - Exponential Moving Average"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "S"
    min_bars = 60

    def _ma(self, c: pd.Series, p: int) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.EMA(c.values, timeperiod=p), index=c.index)
        return _ema(c, p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._ma(c, 21).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, self._ma(c, 9), self._ma(c, 21))


class WMAIndicator(BaseIndicator):
    id = 3
    name = "WMA - Weighted Moving Average"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "B"
    min_bars = 60

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = _wma(c, 20).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, _wma(c, 10), _wma(c, 30))


class HMAIndicator(BaseIndicator):
    id = 4
    name = "HMA - Hull Moving Average"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "A"
    min_bars = 50

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = _hma(c, 21).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, _hma(c, 9), _hma(c, 21))


class DEMAIndicator(BaseIndicator):
    id = 5
    name = "DEMA - Double EMA"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "B"
    min_bars = 60

    def _ma(self, c: pd.Series, p: int) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.DEMA(c.values, timeperiod=p), index=c.index)
        return _dema(c, p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._ma(c, 21).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, self._ma(c, 9), self._ma(c, 21))


class TEMAIndicator(BaseIndicator):
    id = 6
    name = "TEMA - Triple EMA"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "B"
    min_bars = 60

    def _ma(self, c: pd.Series, p: int) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.TEMA(c.values, timeperiod=p), index=c.index)
        return _tema(c, p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._ma(c, 21).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, self._ma(c, 9), self._ma(c, 21))


class KAMAIndicator(BaseIndicator):
    id = 7
    name = "KAMA - Kaufman Adaptive MA"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "A"
    min_bars = 60

    def _ma(self, c: pd.Series, p: int) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.KAMA(c.values, timeperiod=p), index=c.index)
        # تقريب بسيط: EMA
        return _ema(c, p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._ma(c, 21).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, self._ma(c, 10), self._ma(c, 30))


class T3Indicator(BaseIndicator):
    id = 8
    name = "T3 - Tillson T3 MA"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "B"
    min_bars = 60

    def _ma(self, c: pd.Series, p: int) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.T3(c.values, timeperiod=p, vfactor=0.7), index=c.index)
        return _ema(_ema(_ema(c, p), p), p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._ma(c, 14).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, self._ma(c, 8), self._ma(c, 21))


class ALMAIndicator(BaseIndicator):
    id = 9
    name = "ALMA - Arnaud Legoux MA"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "B"
    min_bars = 60

    def _alma(self, c: pd.Series, p: int = 9, sigma: float = 6, offset: float = 0.85) -> pd.Series:
        m = offset * (p - 1)
        s = p / sigma
        weights = np.exp(-((np.arange(p) - m) ** 2) / (2 * s * s))
        weights /= weights.sum()
        return c.rolling(p).apply(lambda x: np.dot(x, weights), raw=True)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._alma(c, 9).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, self._alma(c, 9), self._alma(c, 21))


class ZLEMAIndicator(BaseIndicator):
    id = 10
    name = "ZLEMA - Zero-Lag EMA"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "B"
    min_bars = 60

    def _zlema(self, c: pd.Series, p: int) -> pd.Series:
        lag = (p - 1) // 2
        ema_data = c + (c - c.shift(lag))
        return _ema(ema_data, p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._zlema(c, 21).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        return _trend_signal_from_ma(c, self._zlema(c, 9), self._zlema(c, 21))


class MAMAIndicator(BaseIndicator):
    id = 11
    name = "MAMA - MESA Adaptive MA"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "C"
    min_bars = 60

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        if HAS_TALIB:
            mama, _ = talib.MAMA(c.values, fastlimit=0.5, slowlimit=0.05)
            v = mama[-1] if len(mama) else None
            return float(v) if v is not None and not np.isnan(v) else None
        return float(_ema(c, 21).iloc[-1])

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        if HAS_TALIB:
            mama, fama = talib.MAMA(c.values, fastlimit=0.5, slowlimit=0.05)
            mama_s = pd.Series(mama, index=c.index)
            fama_s = pd.Series(fama, index=c.index)
            return _trend_signal_from_ma(c, mama_s, fama_s)
        return _trend_signal_from_ma(c, _ema(c, 9), _ema(c, 21))


class SupertrendIndicator(BaseIndicator):
    id = 12
    name = "Supertrend"
    category = "مؤشرات الاتجاه"
    category_en = "Trend"
    tier = "S"
    min_bars = 30

    def _supertrend(self, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)
        # ATR
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period, adjust=False).mean()
        # bands
        hl2 = (high + low) / 2.0
        upper = hl2 + multiplier * atr
        lower = hl2 - multiplier * atr
        # final supertrend (تنفيذ مبسّط)
        st = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=int)
        for i in range(len(close)):
            if i == 0:
                st.iloc[i] = upper.iloc[i]
                direction.iloc[i] = -1
                continue
            prev = st.iloc[i - 1]
            if close.iloc[i] > prev:
                direction.iloc[i] = 1
                st.iloc[i] = max(lower.iloc[i], prev) if direction.iloc[i - 1] == 1 else lower.iloc[i]
            else:
                direction.iloc[i] = -1
                st.iloc[i] = min(upper.iloc[i], prev) if direction.iloc[i - 1] == -1 else upper.iloc[i]
        return st, direction

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        st, _ = self._supertrend(df)
        v = st.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        _, direction = self._supertrend(df)
        if pd.isna(direction.iloc[-1]):
            return "محايد"
        return "شراء" if direction.iloc[-1] == 1 else "بيع"
