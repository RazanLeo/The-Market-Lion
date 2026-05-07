"""Fibonacci analysis — retracements + extensions + nearest-level detection on last impulse leg.

Steps:
  1. Find last impulse via ZigZag (min %swing = 1×ATR or 0.8% of close).
  2. Compute retracements: 0, 23.6, 38.2, 50, 61.8, 78.6, 100.
  3. Compute extensions: 127.2, 161.8, 200, 261.8, 423.6.
  4. Locate the closest fib level to current price (within 0.3×ATR).
  5. Bias: buy at 50/61.8/78.6 retracement of an up-leg or extension of a down-leg, etc.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "fibonacci"
WEIGHT_DEFAULT = 1.1


def _last_impulse(df: pd.DataFrame, atr_v: float):
    """Locate most-recent significant swing (high vs low) over last 60 bars."""
    win = df.iloc[-60:]
    h_idx = int(win["h"].argmax()); l_idx = int(win["l"].argmin())
    swing_high = float(win["h"].iloc[h_idx])
    swing_low = float(win["l"].iloc[l_idx])
    if swing_high - swing_low < atr_v * 2:
        return None
    direction = "up" if h_idx > l_idx else "down"
    return {"direction": direction, "high": swing_high, "low": swing_low,
            "high_idx": h_idx, "low_idx": l_idx}


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr_v = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 0)
    if atr_v == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    leg = _last_impulse(df, atr_v)
    if leg is None:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    rng = leg["high"] - leg["low"]
    last = float(df["c"].iloc[-1])

    if leg["direction"] == "up":
        retr = {f"{int(p*1000)/10:.1f}%": leg["high"] - p * rng for p in [0.236, 0.382, 0.5, 0.618, 0.786]}
        ext = {f"{int(p*1000)/10:.1f}%": leg["high"] + (p - 1) * rng for p in [1.272, 1.618, 2.0, 2.618]}
    else:
        retr = {f"{int(p*1000)/10:.1f}%": leg["low"] + p * rng for p in [0.236, 0.382, 0.5, 0.618, 0.786]}
        ext = {f"{int(p*1000)/10:.1f}%": leg["low"] - (p - 1) * rng for p in [1.272, 1.618, 2.0, 2.618]}

    all_levels = {**{f"R{k}": v for k, v in retr.items()}, **{f"E{k}": v for k, v in ext.items()}}
    nearest_name, nearest_price, nearest_dist = None, None, float("inf")
    for name, price in all_levels.items():
        d = abs(last - price)
        if d < nearest_dist:
            nearest_dist = d; nearest_name = name; nearest_price = price

    in_zone = nearest_dist < atr_v * 0.3

    payload = {
        "leg_direction": leg["direction"],
        "swing_high": round(leg["high"], 5), "swing_low": round(leg["low"], 5),
        "retracements": {k: round(v, 5) for k, v in retr.items()},
        "extensions": {k: round(v, 5) for k, v in ext.items()},
        "nearest_level": nearest_name, "nearest_price": round(nearest_price, 5),
        "distance_atr_units": round(nearest_dist / atr_v, 2),
        "in_action_zone": in_zone,
    }

    if not in_zone:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)

    score = 0.0
    if leg["direction"] == "up":
        # Bullish: bouncing at retracement = buy
        if nearest_name and nearest_name.startswith("R"):
            pct_str = nearest_name[1:].replace("%", "")
            try:
                pct = float(pct_str) / 100
                if 0.45 <= pct <= 0.80: score += 35  # golden pocket
                elif 0.30 <= pct < 0.45: score += 15
            except ValueError: pass
        # At an extension above swing high → exhaustion
        if nearest_name and nearest_name.startswith("E"):
            score -= 20
    else:
        if nearest_name and nearest_name.startswith("R"):
            pct_str = nearest_name[1:].replace("%", "")
            try:
                pct = float(pct_str) / 100
                if 0.45 <= pct <= 0.80: score -= 35
                elif 0.30 <= pct < 0.45: score -= 15
            except ValueError: pass
        if nearest_name and nearest_name.startswith("E"):
            score += 20

    if score >= 15:
        return AnalyzerResult(CODE, "buy", min(85.0, 45 + score), WEIGHT_DEFAULT, payload)
    if score <= -15:
        return AnalyzerResult(CODE, "sell", min(85.0, 45 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class FibonacciAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
