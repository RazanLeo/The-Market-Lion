"""ICT Killzones — London Open (02:00-05:00 UTC), NYAM (13:30-16:00 UTC), NYPM (18:00-21:00 UTC).

Track range expansion and direction within the active killzone.
A "killzone breakout" = current bar close beyond the killzone-so-far range AND volume confirmation.
"""
from __future__ import annotations
from datetime import time
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "killzones_london_ny_school"
WEIGHT_DEFAULT = 0.85

KZ = {
    "London":  (time(2, 0), time(5, 0)),
    "NY_AM":   (time(13, 30), time(16, 0)),
    "NY_PM":   (time(18, 0), time(21, 0)),
}


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_ts = df.index[-1]
    cur_t = last_ts.time()
    active = None
    for name, (s, e) in KZ.items():
        if s <= cur_t <= e:
            active = name; break
    payload = {"active_killzone": active}
    if not active:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    # Build bars within today's killzone
    today = last_ts.normalize()
    s, e = KZ[active]
    kz_start = today + pd.Timedelta(hours=s.hour, minutes=s.minute)
    kz_end = today + pd.Timedelta(hours=e.hour, minutes=e.minute)
    in_kz = df[(df.index >= kz_start) & (df.index <= last_ts)]
    if len(in_kz) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    kz_high = float(in_kz["h"].max()); kz_low = float(in_kz["l"].min())
    last_close = float(df["c"].iloc[-1])
    kz_open = float(in_kz["o"].iloc[0])
    direction = "up" if last_close > kz_open else "down"
    # vol confirmation
    avg_v = float(df["v"].rolling(50).mean().iloc[-1] or 1) if "v" in df.columns else 1
    last_v = float(df["v"].iloc[-1]) if "v" in df.columns else avg_v
    breakout_up = last_close >= kz_high * 0.999 and last_v > avg_v * 1.2
    breakout_dn = last_close <= kz_low * 1.001 and last_v > avg_v * 1.2
    payload.update({"kz_open": round(kz_open, 5), "kz_high": round(kz_high, 5),
                    "kz_low": round(kz_low, 5), "direction": direction,
                    "breakout_up": breakout_up, "breakout_down": breakout_dn})
    if breakout_up: return AnalyzerResult(CODE, "buy", 75, WEIGHT_DEFAULT, payload)
    if breakout_dn: return AnalyzerResult(CODE, "sell", 75, WEIGHT_DEFAULT, payload)
    if direction == "up": return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)


class KillzonesLondonNySchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
