"""Inner Circle Trader (ICT) — Killzones, Power of 3, Silver Bullet, Judas Swing, OTE.

All session times in UTC. Killzones (per ICT canon, mapped to UTC):
  • London Open Killzone:   02:00–05:00 UTC
  • New York AM Killzone:   13:30–16:00 UTC
  • New York PM Killzone:   18:00–21:00 UTC
  • London Close:           15:00–17:00 UTC

Constructs:
  • Power of 3 (AMD): Asian session = Accumulation (00:00-06:00),
    London = Manipulation (06:00-12:00), NY = Distribution (12:00-21:00).
  • Silver Bullet: 15-minute window after each Killzone open (high-probability MSS).
  • Judas Swing: false move at session open in opposite direction of the day's bias.
  • OTE (Optimal Trade Entry): 0.62-0.79 retracement of the most recent leg.
"""
from __future__ import annotations
from datetime import datetime, time, timezone
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "ict"
WEIGHT_DEFAULT = 1.3


def _current_killzone(now: datetime) -> str | None:
    h, m = now.hour, now.minute
    t = h * 60 + m
    if 120 <= t < 300: return "London_Open"
    if 810 <= t < 960: return "NY_AM"
    if 900 <= t < 1020: return "London_Close"
    if 1080 <= t < 1260: return "NY_PM"
    return None


def _silver_bullet(now: datetime, kz_start_minutes: int) -> bool:
    cur_min = now.hour * 60 + now.minute
    return kz_start_minutes <= cur_min < kz_start_minutes + 15


def _judas_swing(df: pd.DataFrame) -> dict | None:
    """First 60 minutes of NY session: did price spike one way then reverse fully?"""
    if len(df) < 30:
        return None
    today = df.index[-1].normalize()
    ny_open = today + pd.Timedelta(hours=13, minutes=30)
    ny_window = df[(df.index >= ny_open) & (df.index <= ny_open + pd.Timedelta(minutes=60))]
    if len(ny_window) < 4:
        return None
    open_p = float(ny_window["o"].iloc[0])
    high = float(ny_window["h"].max()); low = float(ny_window["l"].min())
    close = float(ny_window["c"].iloc[-1])
    rng = high - low
    if rng <= 0: return None
    spike_up = (high - open_p) / rng > 0.6 and (close - open_p) < 0
    spike_dn = (open_p - low) / rng > 0.6 and (close - open_p) > 0
    if spike_up: return {"direction": "false_high_then_dn", "high": high, "close": close}
    if spike_dn: return {"direction": "false_low_then_up", "low": low, "close": close}
    return None


def _ote_zone(df: pd.DataFrame) -> dict | None:
    """Last impulse leg using last swing high & low; OTE = retracement to 0.62-0.79."""
    if len(df) < 30:
        return None
    win = df.iloc[-50:]
    h_idx = int(win["h"].argmax()); l_idx = int(win["l"].argmin())
    if h_idx == l_idx:
        return None
    swing_high = float(win["h"].iloc[h_idx])
    swing_low = float(win["l"].iloc[l_idx])
    rng = swing_high - swing_low
    if rng <= 0: return None
    last_close = float(df["c"].iloc[-1])
    if h_idx > l_idx:  # bullish leg
        ote_top = swing_low + rng * 0.79
        ote_bot = swing_low + rng * 0.62
        in_zone = ote_bot <= last_close <= ote_top
        return {"side": "buy", "ote_top": round(ote_top, 5), "ote_bot": round(ote_bot, 5), "in_zone": in_zone}
    ote_top = swing_high - rng * 0.62
    ote_bot = swing_high - rng * 0.79
    in_zone = ote_bot <= last_close <= ote_top
    return {"side": "sell", "ote_top": round(ote_top, 5), "ote_bot": round(ote_bot, 5), "in_zone": in_zone}


def _power_of_three(df: pd.DataFrame) -> dict | None:
    """For today's bars: Asian range, London manipulation (sweep beyond Asian), NY distribution."""
    if len(df) < 96:
        return None
    today = df.index[-1].normalize()
    asia = df[(df.index >= today) & (df.index < today + pd.Timedelta(hours=6))]
    london = df[(df.index >= today + pd.Timedelta(hours=6)) & (df.index < today + pd.Timedelta(hours=12))]
    ny = df[df.index >= today + pd.Timedelta(hours=12)]
    if len(asia) < 4 or len(london) < 2:
        return None
    a_h = float(asia["h"].max()); a_l = float(asia["l"].min())
    l_h = float(london["h"].max()); l_l = float(london["l"].min())
    swept_high = l_h > a_h
    swept_low = l_l < a_l
    distribution = "down" if swept_high else "up" if swept_low else "none"
    return {"asian_high": round(a_h,5), "asian_low": round(a_l,5),
            "london_swept_high": swept_high, "london_swept_low": swept_low,
            "expected_distribution": distribution}


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    now = df.index[-1].to_pydatetime()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    kz = _current_killzone(now)
    sb_london = _silver_bullet(now, 120)
    sb_ny = _silver_bullet(now, 810)
    judas = _judas_swing(df)
    ote = _ote_zone(df)
    p3 = _power_of_three(df)

    payload = {
        "killzone": kz, "silver_bullet_london": sb_london, "silver_bullet_ny": sb_ny,
        "judas": judas, "ote": ote, "power_of_three": p3, "now_utc": now.isoformat(),
    }

    if kz is None and not (judas or (ote and ote["in_zone"])):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)

    score = 0.0
    if ote and ote["in_zone"] and ote["side"] == "buy": score += 25
    if ote and ote["in_zone"] and ote["side"] == "sell": score -= 25
    if judas and judas["direction"] == "false_low_then_up": score += 30
    if judas and judas["direction"] == "false_high_then_dn": score -= 30
    if p3 and p3["expected_distribution"] == "up": score += 18
    if p3 and p3["expected_distribution"] == "down": score -= 18
    if sb_ny: score *= 1.2
    if kz in ("NY_AM", "London_Open") and abs(score) > 0: score *= 1.1

    if score >= 25:
        return AnalyzerResult(CODE, "buy", min(90.0, 50 + score), WEIGHT_DEFAULT, payload)
    if score <= -25:
        return AnalyzerResult(CODE, "sell", min(90.0, 50 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class IctAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
