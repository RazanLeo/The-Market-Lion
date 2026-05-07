# ═══════════════════════════════════════════════════════════════════════════
# 🦁 المؤشر #17 — ADX + DMI (Average Directional Index) — Tier S
# الاستراتيجية: ADX > 25 + +DI > -DI = شراء قوي
#               ADX > 25 + -DI > +DI = بيع قوي
#               ADX < 20 = سوق جانبي (محايد)
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
from app.indicators.base import BaseIndicator

try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False


def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """تنعيم Wilder (مكافئ لـ TA-Lib عند استخدام alpha=1/period)"""
    return series.ewm(alpha=1 / period, adjust=False).mean()


def _adx_dmi_pandas(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    """ADX + DMI fallback بدون TA-Lib"""
    up = high.diff()
    down = -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=high.index)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = _wilder_smooth(tr, period)
    plus_di = 100 * _wilder_smooth(plus_dm, period) / atr.replace(0, np.nan)
    minus_di = 100 * _wilder_smooth(minus_dm, period) / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = _wilder_smooth(dx, period)
    return adx, plus_di, minus_di


class ADXDMIIndicator(BaseIndicator):
    id = 17
    name = "ADX + DMI - Average Directional Index"
    category = "مؤشرات الزخم"
    category_en = "Momentum"
    tier = "S"
    min_bars = 35

    def _compute(self, df: pd.DataFrame):
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)
        if HAS_TALIB:
            adx = pd.Series(talib.ADX(high.values, low.values, close.values, timeperiod=14), index=close.index)
            plus_di = pd.Series(talib.PLUS_DI(high.values, low.values, close.values, timeperiod=14), index=close.index)
            minus_di = pd.Series(talib.MINUS_DI(high.values, low.values, close.values, timeperiod=14), index=close.index)
            return adx, plus_di, minus_di
        return _adx_dmi_pandas(high, low, close, 14)

    def compute_raw_value(self, df: pd.DataFrame) -> float:
        adx, _, _ = self._compute(df)
        v = adx.iloc[-1]
        return float(v) if pd.notna(v) else None

    def compute_signal(self, df: pd.DataFrame) -> str:
        adx, plus_di, minus_di = self._compute(df)
        if pd.isna(adx.iloc[-1]) or pd.isna(plus_di.iloc[-1]) or pd.isna(minus_di.iloc[-1]):
            return "محايد"

        last_adx = adx.iloc[-1]
        last_pdi = plus_di.iloc[-1]
        last_mdi = minus_di.iloc[-1]

        # سوق جانبي
        if last_adx < 20:
            return "محايد"
        # اتجاه قوي
        if last_adx > 25:
            if last_pdi > last_mdi:
                return "شراء"
            if last_mdi > last_pdi:
                return "بيع"
        # منطقة انتقالية 20-25
        if last_pdi > last_mdi * 1.1:
            return "شراء"
        if last_mdi > last_pdi * 1.1:
            return "بيع"
        return "محايد"
