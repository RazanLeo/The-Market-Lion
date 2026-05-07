"""Session Analysis — Asian / London / NY session ranges + overlap volatility.

Sessions in UTC:
  • Asian:  00:00 – 08:00
  • London: 07:00 – 16:00
  • NY:     12:00 – 21:00
  • London-NY overlap: 12:00 – 16:00 (max liquidity).

Identify the active session, compute its range so far vs previous-day same-session range.
A "session expansion" = current session range > 1.3× previous-day session range → momentum continues.
"""
from __future__ import annotations
from datetime import time
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "session_analysis"
WEIGHT_DEFAULT = 0.85


def _session_of(t: pd.Timestamp) -> str:
    h = t.hour
    if 0 <= h < 7: return "Asian"
    if 7 <= h < 12: return "London"
    if 12 <= h < 16: return "London_NY_overlap"
    if 16 <= h < 21: return "NY"
    return "off"


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 96 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_ts = df.index[-1]
    cur_session = _session_of(last_ts)
    today = last_ts.normalize()
    # Build per-session bins for today and yesterday
    out = {}
    for label, (sh, eh) in {
        "Asian": (0, 7), "London": (7, 12), "Overlap": (12, 16), "NY": (16, 21)
    }.items():
        td = df[(df.index >= today + pd.Timedelta(hours=sh)) & (df.index < today + pd.Timedelta(hours=eh))]
        yd = df[(df.index >= today - pd.Timedelta(days=1) + pd.Timedelta(hours=sh)) &
                (df.index < today - pd.Timedelta(days=1) + pd.Timedelta(hours=eh))]
        td_rng = float(td["h"].max() - td["l"].min()) if len(td) else 0
        yd_rng = float(yd["h"].max() - yd["l"].min()) if len(yd) else td_rng or 1
        out[label] = {"today_range": round(td_rng, 5),
                      "yesterday_range": round(yd_rng, 5),
                      "expansion_ratio": round(td_rng / max(yd_rng, 1e-9), 2)}
    expansion = (out.get(cur_session.split("_")[0], {}).get("expansion_ratio", 1)
                 if cur_session != "off" else 1)
    last = float(df["c"].iloc[-1])
    open_session = float(df[(df.index >= today) & (df.index <= last_ts)]["o"].iloc[0]) if len(
        df[(df.index >= today) & (df.index <= last_ts)]) else last
    direction = "up" if last > open_session else "down"
    payload = {"active_session": cur_session, "sessions": out,
               "current_expansion_ratio": expansion, "direction_from_open": direction}
    if expansion > 1.3 and direction == "up":
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if expansion > 1.3 and direction == "down":
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SessionAnalysisAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
