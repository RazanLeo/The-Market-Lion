# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشرات #31..#39 — مؤشرات التذبذب الإضافية
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


def _atr(df: pd.DataFrame, p: int = 14) -> pd.Series:
    h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
    tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/p, adjust=False).mean()


# ─────────────────────────────────────────────────────────────────────────────
class KeltnerChannelsIndicator(BaseIndicator):
    """#31 — Keltner Channels"""
    id = 31
    name = "Keltner Channels"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "A"
    min_bars = 25

    def _kc(self, df: pd.DataFrame, period: int = 20, mult: float = 2.0):
        c = df["close"].astype(float)
        ema = _ema(c, period)
        atr = _atr(df, period)
        return ema + mult * atr, ema, ema - mult * atr

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        upper, mid, lower = self._kc(df)
        c = df["close"].astype(float)
        denom = upper.iloc[-1] - lower.iloc[-1]
        if denom == 0 or pd.isna(denom): return None
        return float((c.iloc[-1] - lower.iloc[-1]) / denom)

    def compute_signal(self, df: pd.DataFrame) -> str:
        upper, mid, lower = self._kc(df)
        c = df["close"].astype(float)
        if pd.isna(upper.iloc[-1]): return "محايد"
        if c.iloc[-1] > upper.iloc[-1]: return "شراء"
        if c.iloc[-1] < lower.iloc[-1]: return "بيع"
        if c.iloc[-1] > mid.iloc[-1] and c.iloc[-2] <= mid.iloc[-2]: return "شراء"
        if c.iloc[-1] < mid.iloc[-1] and c.iloc[-2] >= mid.iloc[-2]: return "بيع"
        return "محايد"


class DonchianChannelsIndicator(BaseIndicator):
    """#32 — Donchian Channels"""
    id = 32
    name = "Donchian Channels"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "B"
    min_bars = 25

    def _dc(self, df: pd.DataFrame, period: int = 20):
        h = df["high"].astype(float); l = df["low"].astype(float)
        upper = h.rolling(period).max()
        lower = l.rolling(period).min()
        mid = (upper + lower) / 2.0
        return upper, mid, lower

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        upper, mid, lower = self._dc(df)
        c = df["close"].astype(float)
        denom = upper.iloc[-1] - lower.iloc[-1]
        if denom == 0 or pd.isna(denom): return None
        return float((c.iloc[-1] - lower.iloc[-1]) / denom)

    def compute_signal(self, df: pd.DataFrame) -> str:
        upper, mid, lower = self._dc(df)
        c = df["close"].astype(float)
        if pd.isna(upper.iloc[-1]): return "محايد"
        # كسر القمم/القيعان
        if c.iloc[-1] >= upper.iloc[-2]: return "شراء"
        if c.iloc[-1] <= lower.iloc[-2]: return "بيع"
        return "محايد"


class StarcBandsIndicator(BaseIndicator):
    """#33 — STARC Bands"""
    id = 33
    name = "STARC Bands"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "C"
    min_bars = 30

    def _starc(self, df: pd.DataFrame, period: int = 15, mult: float = 2.0):
        c = df["close"].astype(float)
        sma = c.rolling(period).mean()
        atr = _atr(df, period)
        return sma + mult * atr, sma, sma - mult * atr

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        upper, mid, lower = self._starc(df)
        c = df["close"].astype(float)
        denom = upper.iloc[-1] - lower.iloc[-1]
        if denom == 0 or pd.isna(denom): return None
        return float((c.iloc[-1] - lower.iloc[-1]) / denom)

    def compute_signal(self, df: pd.DataFrame) -> str:
        upper, mid, lower = self._starc(df)
        c = df["close"].astype(float)
        if pd.isna(upper.iloc[-1]): return "محايد"
        if c.iloc[-1] < lower.iloc[-1]: return "شراء"
        if c.iloc[-1] > upper.iloc[-1]: return "بيع"
        return "محايد"


class StdDevIndicator(BaseIndicator):
    """#34 — Standard Deviation"""
    id = 34
    name = "Standard Deviation"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "C"
    min_bars = 25

    def _std(self, c: pd.Series, p: int = 20) -> pd.Series:
        if HAS_TALIB:
            return pd.Series(talib.STDDEV(c.values, timeperiod=p, nbdev=1), index=c.index)
        return c.rolling(p).std(ddof=0)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._std(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        # تذبذب عالٍ + سعر صاعد = شراء، تذبذب عالٍ + سعر هابط = بيع
        c = df["close"].astype(float)
        s = self._std(c)
        if len(s) < 22 or pd.isna(s.iloc[-1]): return "محايد"
        rising_vol = s.iloc[-1] > s.iloc[-5:].mean() * 1.1
        price_up = c.iloc[-1] > c.iloc[-10]
        if rising_vol and price_up: return "شراء"
        if rising_vol and not price_up: return "بيع"
        return "محايد"


class HistVolatilityIndicator(BaseIndicator):
    """#35 — Historical Volatility"""
    id = 35
    name = "Historical Volatility"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "C"
    min_bars = 25

    def _hv(self, c: pd.Series, p: int = 20) -> pd.Series:
        log_ret = np.log(c / c.shift())
        return log_ret.rolling(p).std(ddof=0) * np.sqrt(252)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._hv(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        h = self._hv(c)
        if pd.isna(h.iloc[-1]): return "محايد"
        # تذبذب منخفض + اختراق = إشارة قوية
        if h.iloc[-1] < h.iloc[-20:].mean() * 0.7:
            if c.iloc[-1] > c.iloc[-2]: return "شراء"
            if c.iloc[-1] < c.iloc[-2]: return "بيع"
        return "محايد"


class ChaikinVolIndicator(BaseIndicator):
    """#36 — Chaikin Volatility"""
    id = 36
    name = "Chaikin Volatility"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "C"
    min_bars = 25

    def _cv(self, df: pd.DataFrame, ema_p: int = 10, change_p: int = 10) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float)
        hl_ema = _ema(h - l, ema_p)
        return ((hl_ema - hl_ema.shift(change_p)) / hl_ema.shift(change_p) * 100)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._cv(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        cv = self._cv(df)
        if pd.isna(cv.iloc[-1]): return "محايد"
        if cv.iloc[-1] > 0 and c.iloc[-1] > c.iloc[-5]: return "شراء"
        if cv.iloc[-1] > 0 and c.iloc[-1] < c.iloc[-5]: return "بيع"
        return "محايد"


class UlcerIndexIndicator(BaseIndicator):
    """#37 — Ulcer Index"""
    id = 37
    name = "Ulcer Index"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "C"
    min_bars = 25

    def _ulcer(self, c: pd.Series, p: int = 14) -> pd.Series:
        max_close = c.rolling(p).max()
        drawdown = 100 * (c - max_close) / max_close.replace(0, np.nan)
        return np.sqrt((drawdown ** 2).rolling(p).mean())

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        c = df["close"].astype(float)
        v = self._ulcer(c).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        u = self._ulcer(c)
        if pd.isna(u.iloc[-1]): return "محايد"
        # Ulcer منخفض + سعر صاعد = شراء
        low_stress = u.iloc[-1] < u.iloc[-20:].mean() * 0.8
        if low_stress and c.iloc[-1] > c.iloc[-5]: return "شراء"
        if not low_stress and c.iloc[-1] < c.iloc[-5]: return "بيع"
        return "محايد"


class MassIndexIndicator(BaseIndicator):
    """#38 — Mass Index"""
    id = 38
    name = "Mass Index"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "C"
    min_bars = 30

    def _mi(self, df: pd.DataFrame, ema_p: int = 9, sum_p: int = 25) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float)
        ema1 = _ema(h - l, ema_p)
        ema2 = _ema(ema1, ema_p)
        return (ema1 / ema2.replace(0, np.nan)).rolling(sum_p).sum()

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._mi(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        c = df["close"].astype(float)
        m = self._mi(df)
        if pd.isna(m.iloc[-1]): return "محايد"
        # انعكاس محتمل عند Mass > 27
        if m.iloc[-1] > 27 and m.iloc[-2] <= 27:
            if c.iloc[-1] > c.iloc[-5]: return "بيع"  # انعكاس هبوطي
            else: return "شراء"  # انعكاس صعودي
        return "محايد"


class ChoppinessIndexIndicator(BaseIndicator):
    """#39 — Choppiness Index"""
    id = 39
    name = "Choppiness Index"
    category = "مؤشرات التذبذب"
    category_en = "Volatility"
    tier = "A"
    min_bars = 25

    def _ci(self, df: pd.DataFrame, p: int = 14) -> pd.Series:
        h = df["high"].astype(float); l = df["low"].astype(float); c = df["close"].astype(float)
        atr_sum = _atr(df, 1).rolling(p).sum()
        rng = h.rolling(p).max() - l.rolling(p).min()
        ratio = atr_sum / rng.replace(0, np.nan)
        return 100 * np.log10(ratio) / np.log10(p)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        v = self._ci(df).iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        # Choppiness > 61.8 = جانبي → محايد قوي
        # Choppiness < 38.2 = اتجاه قوي → اتبع السعر
        c = df["close"].astype(float)
        ci = self._ci(df)
        if pd.isna(ci.iloc[-1]): return "محايد"
        if ci.iloc[-1] > 61.8: return "محايد"
        if ci.iloc[-1] < 38.2:
            if c.iloc[-1] > c.iloc[-10]: return "شراء"
            if c.iloc[-1] < c.iloc[-10]: return "بيع"
        return "محايد"
