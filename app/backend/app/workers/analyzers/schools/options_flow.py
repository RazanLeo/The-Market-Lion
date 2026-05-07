"""Options Flow proxy — detect unusual implied moves indicating large option positioning.

A 1-bar move > 2× ATR(14) on volume > 1.5× avg suggests:
  • Hedging activity behind it (gamma squeeze, large delta hedge).
  • Direction = sign of bar close-open.
We track the bar and the follow-through 3 bars after.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "options_flow"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l, c, o = df["h"], df["l"], df["c"], df["o"]
    body = (c - o)
    abs_body = body.abs()
    atr = float((h - l).rolling(14).mean().iloc[-1] or 1)
    avg_v = float(df["v"].rolling(50).mean().iloc[-1] or 1)
    last_body = float(abs_body.iloc[-1])
    last_v = float(df["v"].iloc[-1])
    unusual = last_body > 2 * atr and last_v > 1.5 * avg_v
    direction = "up" if float(body.iloc[-1]) > 0 else "down"
    # Follow-through over last 3 bars
    short_drift = float(c.iloc[-1] - c.iloc[-4]) if len(c) > 4 else 0
    payload = {"unusual_move": unusual, "direction": direction,
               "body_in_atr_units": round(last_body / atr, 2),
               "vol_ratio": round(last_v / avg_v, 2),
               "short_drift": round(short_drift, 5)}
    if unusual and direction == "up": return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if unusual and direction == "down": return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class OptionsFlowAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
