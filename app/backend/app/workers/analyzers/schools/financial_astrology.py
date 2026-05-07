"""Financial Astrology — lunar cycle (29.53-day) + Mercury retrograde windows.

Lunar phase via simplified Meeus algorithm: phase = (JD - 2451550.1) mod 29.530588853 / 29.530588853.
0/1 = New moon; 0.5 = Full moon. Turning points expected near new/full moon.
Mercury retrograde windows are encoded as a static table for 2024-2027 (3-4 per year).
"""
from __future__ import annotations
from datetime import datetime, timezone, date
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "financial_astrology"
WEIGHT_DEFAULT = 0.5

MERCURY_RETROGRADE = [
    (date(2024, 4, 1),  date(2024, 4, 25)),
    (date(2024, 8, 5),  date(2024, 8, 28)),
    (date(2024, 11, 26),date(2024, 12, 15)),
    (date(2025, 3, 15), date(2025, 4, 7)),
    (date(2025, 7, 18), date(2025, 8, 11)),
    (date(2025, 11, 9), date(2025, 11, 29)),
    (date(2026, 2, 26), date(2026, 3, 20)),
    (date(2026, 6, 29), date(2026, 7, 23)),
    (date(2026, 10, 24),date(2026, 11, 13)),
    (date(2027, 2, 9),  date(2027, 3, 3)),
    (date(2027, 6, 11), date(2027, 7, 5)),
    (date(2027, 10, 7), date(2027, 10, 28)),
]


def _julian_day(dt: datetime) -> float:
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    frac = (dt.hour + dt.minute / 60 + dt.second / 3600) / 24 - 0.5
    return jdn + frac


def _lunar_phase(dt: datetime) -> float:
    jd = _julian_day(dt)
    return ((jd - 2451550.1) % 29.530588853) / 29.530588853


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if not isinstance(df.index, pd.DatetimeIndex) or len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_ts = df.index[-1].to_pydatetime()
    if last_ts.tzinfo is None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    phase = _lunar_phase(last_ts)
    cur_date = last_ts.date()
    in_retro = any(s <= cur_date <= e for s, e in MERCURY_RETROGRADE)
    near_new = phase < 0.05 or phase > 0.95
    near_full = abs(phase - 0.5) < 0.05
    direction_up = float(df["c"].iloc[-1]) > float(df["c"].iloc[-10])
    payload = {"lunar_phase": round(phase, 3), "near_new_moon": near_new,
               "near_full_moon": near_full, "mercury_retrograde": in_retro,
               "trend_now": "up" if direction_up else "down"}
    if near_new and not direction_up:
        return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if near_full and direction_up:
        return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    if in_retro: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {**payload, "warning": "high_volatility_window"})
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class FinancialAstrologyAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
