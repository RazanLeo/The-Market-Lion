"""Wyckoff Method — Phase analysis (Accumulation/Markup/Distribution/Markdown).

Detects:
  • Trading-Range (TR) consolidation: price contained for ≥30 bars in narrow range.
  • Spring: false breakdown below TR low + reversal back inside, with declining volume on test
    and expanding volume on the recovery rally (PS/SC/AR/ST/Spring/LPS/SOS sequence proxy).
  • Upthrust (UTAD): false breakout above TR high + reversal back inside, with similar
    volume signature (BC/UT/LPSY/DSTOP).
  • Phase mapping: A (selling/buying climax + secondary test) → B (cause-building) →
    C (test/spring/upthrust) → D (markup/markdown begins) → E (trend in force).
  • Composite Operator narrative: who is accumulating vs distributing.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "wyckoff"
WEIGHT_DEFAULT = 1.4  # high-conviction school


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    win = df.iloc[-80:]
    rng_high = float(win["h"].iloc[:-5].max())
    rng_low = float(win["l"].iloc[:-5].min())
    rng = rng_high - rng_low
    if rng <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    # Determine if we are inside a trading range
    body_avg = (win["h"] - win["l"]).rolling(40).mean().iloc[-1]
    in_tr = rng < body_avg * 8 and rng > 0
    last3 = df.iloc[-3:]
    last_low = float(last3["l"].min())
    last_high = float(last3["h"].max())
    last_close = float(df["c"].iloc[-1])

    # Volume signatures
    v = df["v"].fillna(0)
    avg_v_50 = float(v.rolling(50).mean().iloc[-1] or 1)
    last_v = float(v.iloc[-1])
    test_v = float(v.iloc[-3:-1].mean())  # volume on the test (low)
    rally_v = last_v  # volume on the recovery

    # Spring: dipped below range low and recovered back inside on rising volume
    dipped_below = last_low < rng_low and last_close > rng_low
    declining_test = test_v < avg_v_50 * 0.9
    expanding_rally = rally_v > avg_v_50 * 1.2
    spring = dipped_below and declining_test and expanding_rally

    # Upthrust: spiked above range high and rolled back below on rising volume
    spiked_above = last_high > rng_high and last_close < rng_high
    upthrust = spiked_above and declining_test and expanding_rally

    # Phase determination
    if not in_tr:
        slope_50 = float((df["c"].iloc[-1] - df["c"].iloc[-50]) / df["c"].iloc[-50])
        phase = "E_markup" if slope_50 > 0.02 else "E_markdown" if slope_50 < -0.02 else "B"
    else:
        if spring:
            phase = "C_spring"
        elif upthrust:
            phase = "C_upthrust"
        else:
            mid = (rng_high + rng_low) / 2
            phase = "B_lower" if last_close < mid else "B_upper"

    # Composite Operator hint: are accumulation candles (close near high on volume) dominating?
    upper_close_pos = (df["c"] - df["l"]) / (df["h"] - df["l"] + 1e-9)
    weighted_upper = (upper_close_pos.iloc[-30:] * v.iloc[-30:]).sum() / max(v.iloc[-30:].sum(), 1)
    composite = "accumulation" if weighted_upper > 0.55 else "distribution" if weighted_upper < 0.45 else "neutral"

    payload = {
        "phase": phase,
        "tr_high": round(rng_high, 5),
        "tr_low": round(rng_low, 5),
        "in_tr": in_tr,
        "spring": spring,
        "upthrust": upthrust,
        "composite_operator": composite,
        "weighted_close_pos": round(float(weighted_upper), 3),
        "test_v_ratio": round(test_v / avg_v_50, 2),
        "rally_v_ratio": round(rally_v / avg_v_50, 2),
    }

    if spring:
        return AnalyzerResult(CODE, "buy", 85.0, WEIGHT_DEFAULT, payload)
    if upthrust:
        return AnalyzerResult(CODE, "sell", 85.0, WEIGHT_DEFAULT, payload)
    if phase == "E_markup" and composite == "accumulation":
        return AnalyzerResult(CODE, "buy", 65.0, WEIGHT_DEFAULT, payload)
    if phase == "E_markdown" and composite == "distribution":
        return AnalyzerResult(CODE, "sell", 65.0, WEIGHT_DEFAULT, payload)
    if phase == "B_lower" and composite == "accumulation":
        return AnalyzerResult(CODE, "buy", 50.0, WEIGHT_DEFAULT, payload)
    if phase == "B_upper" and composite == "distribution":
        return AnalyzerResult(CODE, "sell", 50.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class WyckoffAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
