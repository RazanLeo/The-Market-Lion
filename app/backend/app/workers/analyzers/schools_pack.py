"""Schools analyzers — production implementations of 9 schools used at launch.

Implements: SMC, Wyckoff (basic), Fibonacci Retracement, Elliott (basic),
Supply/Demand, Killzones, Power of 3, OTE 61.8%, Pairs Z-Score.
"""
from __future__ import annotations
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from ..engines.voting_engine import AnalyzerResult


# ── helpers ─────────────────────────────────────────────────────────
def _swings(df: pd.DataFrame, n: int = 5) -> tuple[list[int], list[int]]:
    """Returns indices of swing highs and lows using fractal of size n."""
    highs, lows = [], []
    for i in range(n, len(df) - n):
        win_h = df["h"].iloc[i - n:i + n + 1]
        win_l = df["l"].iloc[i - n:i + n + 1]
        if df["h"].iloc[i] == win_h.max(): highs.append(i)
        if df["l"].iloc[i] == win_l.min(): lows.append(i)
    return highs, lows


# ── SMC ────────────────────────────────────────────────────────────
def smc_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("smc", "neutral", 0, 1.0, {})
    highs, lows = _swings(df, 3)
    if len(highs) < 2 or len(lows) < 2:
        return AnalyzerResult("smc", "neutral", 0, 1.0, {})
    last_high = df["h"].iloc[highs[-1]]
    prev_high = df["h"].iloc[highs[-2]]
    last_low = df["l"].iloc[lows[-1]]
    prev_low = df["l"].iloc[lows[-2]]
    last_close = df["c"].iloc[-1]
    # BOS detection
    bos_up = last_close > prev_high
    bos_dn = last_close < prev_low
    structure = "HH+HL" if last_high > prev_high and last_low > prev_low else \
                "LL+LH" if last_high < prev_high and last_low < prev_low else "mixed"
    payload = {"bos_up": bos_up, "bos_dn": bos_dn, "structure": structure,
               "swing_high": float(last_high), "swing_low": float(last_low)}
    if bos_up and structure == "HH+HL":
        return AnalyzerResult("smc", "buy", 80, 1.0, payload)
    if bos_dn and structure == "LL+LH":
        return AnalyzerResult("smc", "sell", 80, 1.0, payload)
    if structure == "HH+HL":
        return AnalyzerResult("smc", "buy", 55, 1.0, payload)
    if structure == "LL+LH":
        return AnalyzerResult("smc", "sell", 55, 1.0, payload)
    return AnalyzerResult("smc", "neutral", 0, 1.0, payload)


# ── Wyckoff (simplified phase detection) ────────────────────────────
def wyckoff_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 100: return AnalyzerResult("wyckoff", "neutral", 0, 1.0, {})
    win = df.iloc[-100:]
    rng = (win["h"].max() - win["l"].min())
    rng_med = (df["h"].rolling(100).max() - df["l"].rolling(100).min()).median()
    is_range = rng < rng_med * 1.2
    if not is_range:
        return AnalyzerResult("wyckoff", "neutral", 0, 1.0, {"is_range": False})
    # spring: low penetrates range low then closes back inside
    range_low = win["l"].iloc[:-1].min()
    range_high = win["h"].iloc[:-1].max()
    last = df.iloc[-1]
    spring = last["l"] < range_low and last["c"] > range_low
    upthrust = last["h"] > range_high and last["c"] < range_high
    if spring:
        return AnalyzerResult("wyckoff", "buy", 70, 1.0, {"phase": "spring"})
    if upthrust:
        return AnalyzerResult("wyckoff", "sell", 70, 1.0, {"phase": "upthrust"})
    return AnalyzerResult("wyckoff", "neutral", 0, 1.0, {"phase": "consolidation"})


# ── Fibonacci Retracement (61.8% bounce) ────────────────────────────
def fib_retracement_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("fib_retracement", "neutral", 0, 1.0, {})
    swing_high = df["h"].iloc[-50:].max()
    swing_low = df["l"].iloc[-50:].min()
    rng = swing_high - swing_low
    fib_618_up = swing_low + rng * 0.618
    fib_618_dn = swing_high - rng * 0.618
    last = df["c"].iloc[-1]
    tol = rng * 0.005
    if abs(last - fib_618_dn) < tol:
        return AnalyzerResult("fib_retracement", "buy", 70, 1.0, {"level": float(fib_618_dn), "trend": "up"})
    if abs(last - fib_618_up) < tol:
        return AnalyzerResult("fib_retracement", "sell", 70, 1.0, {"level": float(fib_618_up), "trend": "down"})
    return AnalyzerResult("fib_retracement", "neutral", 0, 1.0, {"swing_high": float(swing_high), "swing_low": float(swing_low)})


# ── Elliott (basic 1-2-3-4-5 pattern detection) ─────────────────────
def elliott_basic_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80: return AnalyzerResult("elliott", "neutral", 0, 1.0, {})
    highs, lows = _swings(df, 5)
    pivots = sorted(highs + lows)
    if len(pivots) < 5: return AnalyzerResult("elliott", "neutral", 0, 1.0, {})
    last_5 = pivots[-5:]
    prices = [df["c"].iloc[i] for i in last_5]
    # crude: alternating up/down with wave 3 longest
    diffs = [prices[i+1] - prices[i] for i in range(4)]
    up_count = sum(1 for d in diffs if d > 0)
    down_count = 4 - up_count
    bullish_pattern = diffs[0] > 0 and diffs[2] > 0 and abs(diffs[2]) > abs(diffs[0])
    bearish_pattern = diffs[0] < 0 and diffs[2] < 0 and abs(diffs[2]) > abs(diffs[0])
    if bullish_pattern:
        return AnalyzerResult("elliott", "buy", 50, 1.0, {"pattern": "wave3_up"})
    if bearish_pattern:
        return AnalyzerResult("elliott", "sell", 50, 1.0, {"pattern": "wave3_down"})
    return AnalyzerResult("elliott", "neutral", 0, 1.0, {})


# ── Supply / Demand zones ───────────────────────────────────────────
def supply_demand_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("supply_demand", "neutral", 0, 1.0, {})
    body = (df["c"] - df["o"]).abs()
    range_ = df["h"] - df["l"]
    is_explosive = body > body.rolling(20).mean() * 2
    last_idx = -1
    for i in range(-10, -50, -1):
        if is_explosive.iloc[i]:
            base = df.iloc[i-3:i]
            zone_high = float(base["h"].max())
            zone_low = float(base["l"].min())
            if df["c"].iloc[i] > df["o"].iloc[i]:  # bullish impulse → demand zone
                if df["l"].iloc[-1] <= zone_high and df["c"].iloc[-1] >= zone_low:
                    return AnalyzerResult("supply_demand", "buy", 70, 1.0, {"zone": [zone_low, zone_high], "type": "demand"})
            else:  # supply zone
                if df["h"].iloc[-1] >= zone_low and df["c"].iloc[-1] <= zone_high:
                    return AnalyzerResult("supply_demand", "sell", 70, 1.0, {"zone": [zone_low, zone_high], "type": "supply"})
            break
    return AnalyzerResult("supply_demand", "neutral", 0, 1.0, {})


# ── Killzone (London / NY) ─────────────────────────────────────────
LONDON_OPEN = (7, 10)   # UTC
NY_OPEN = (13, 16)      # UTC


def killzone_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    now = datetime.now(timezone.utc)
    h = now.hour
    in_london = LONDON_OPEN[0] <= h < LONDON_OPEN[1]
    in_ny = NY_OPEN[0] <= h < NY_OPEN[1]
    if not (in_london or in_ny):
        return AnalyzerResult("killzone", "neutral", 0, 1.0, {"window": "off"})
    if len(df) < 30: return AnalyzerResult("killzone", "neutral", 0, 1.0, {})
    win = df.iloc[-12:]
    direction = "buy" if win["c"].iloc[-1] > win["o"].iloc[0] else "sell"
    return AnalyzerResult("killzone", direction, 50, 1.0, {"window": "london" if in_london else "ny"})


# ── Power of 3 (Asian Acc → London Manip → NY Distrib) ──────────────
def power_of_three_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    now = datetime.now(timezone.utc)
    if not (NY_OPEN[0] <= now.hour < NY_OPEN[1]):
        return AnalyzerResult("power_of_three", "neutral", 0, 1.0, {"window": "wait_ny"})
    if len(df) < 96: return AnalyzerResult("power_of_three", "neutral", 0, 1.0, {})
    asia_range = df.iloc[-96:-48]
    london_range = df.iloc[-48:-24]
    asia_high = asia_range["h"].max(); asia_low = asia_range["l"].min()
    london_high = london_range["h"].max(); london_low = london_range["l"].min()
    last = df["c"].iloc[-1]
    if london_high > asia_high and last < asia_high:
        return AnalyzerResult("power_of_three", "sell", 70, 1.0, {"phase": "manip_high_then_distribute"})
    if london_low < asia_low and last > asia_low:
        return AnalyzerResult("power_of_three", "buy", 70, 1.0, {"phase": "manip_low_then_distribute"})
    return AnalyzerResult("power_of_three", "neutral", 0, 1.0, {})


# ── OTE 61.8% ──────────────────────────────────────────────────────
def ote_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("ote_61_8", "neutral", 0, 1.0, {})
    swing_h = df["h"].iloc[-30:].max()
    swing_l = df["l"].iloc[-30:].min()
    rng = swing_h - swing_l
    ote_buy = swing_h - rng * 0.618
    ote_sell = swing_l + rng * 0.618
    last = df["c"].iloc[-1]
    tol = rng * 0.01
    if abs(last - ote_buy) <= tol and df["c"].iloc[-2] < df["c"].iloc[-1]:
        return AnalyzerResult("ote_61_8", "buy", 75, 1.0, {"level": float(ote_buy)})
    if abs(last - ote_sell) <= tol and df["c"].iloc[-2] > df["c"].iloc[-1]:
        return AnalyzerResult("ote_61_8", "sell", 75, 1.0, {"level": float(ote_sell)})
    return AnalyzerResult("ote_61_8", "neutral", 0, 1.0, {})


# ── Pairs / Z-Score (mean reversion) ───────────────────────────────
def pairs_zscore_analyzer(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult("pairs_zscore", "neutral", 0, 1.0, {})
    c = df["c"]
    z = (c - c.rolling(50).mean()) / (c.rolling(50).std().replace(0, np.nan))
    z_last = float(z.iloc[-1])
    if z_last < -2.0:
        return AnalyzerResult("pairs_zscore", "buy", min(85, 50 + abs(z_last) * 15), 1.0, {"z": z_last})
    if z_last > 2.0:
        return AnalyzerResult("pairs_zscore", "sell", min(85, 50 + abs(z_last) * 15), 1.0, {"z": z_last})
    return AnalyzerResult("pairs_zscore", "neutral", 0, 1.0, {"z": z_last})
