"""Lion ARC Breakout — Market Lion proprietary.

Detect price breaking the previous 50-bar swing high or low ("ARC of breakout"),
then measure follow-through quality:
  • Breakout volume > 1.5× 50-bar avg.
  • Bar close at ≥ 70% of bar range (in the breakout direction).
  • Within 3 bars after breakout: no close back through the broken level.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_arc_breakout"
WEIGHT_DEFAULT = 1.05


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c, o = df["h"], df["l"], df["c"], df["o"]
    h50 = float(h.iloc[-51:-1].max()); l50 = float(l.iloc[-51:-1].min())
    last_h = float(h.iloc[-1]); last_l = float(l.iloc[-1]); last_c = float(c.iloc[-1])
    last_o = float(o.iloc[-1])
    rng = max(last_h - last_l, 1e-9)
    close_pos_in_bar = (last_c - last_l) / rng
    avg_v = float(df["v"].rolling(50).mean().iloc[-1] or 1)
    last_v = float(df["v"].iloc[-1])
    arc_up = last_c > h50
    arc_dn = last_c < l50
    vol_ok = last_v > avg_v * 1.5
    quality_up = close_pos_in_bar >= 0.7
    quality_dn = close_pos_in_bar <= 0.3
    # Confirmation: last 3 bars stayed beyond breakout level
    post = df.iloc[-3:]
    confirmed_up = arc_up and float(post["c"].min()) > h50
    confirmed_dn = arc_dn and float(post["c"].max()) < l50
    payload = {"50bar_high": round(h50, 5), "50bar_low": round(l50, 5),
               "arc_up": arc_up, "arc_dn": arc_dn,
               "volume_confirms": vol_ok, "close_quality_up": quality_up,
               "close_quality_dn": quality_dn,
               "confirmed_up_3bar": confirmed_up, "confirmed_dn_3bar": confirmed_dn}
    if arc_up and vol_ok and quality_up: return AnalyzerResult(CODE, "buy", 85, WEIGHT_DEFAULT, payload)
    if arc_dn and vol_ok and quality_dn: return AnalyzerResult(CODE, "sell", 85, WEIGHT_DEFAULT, payload)
    if confirmed_up: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if confirmed_dn: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if arc_up: return AnalyzerResult(CODE, "buy", 45, WEIGHT_DEFAULT, payload)
    if arc_dn: return AnalyzerResult(CODE, "sell", 45, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionArcBreakoutAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
