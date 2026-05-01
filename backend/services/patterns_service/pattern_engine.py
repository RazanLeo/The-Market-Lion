"""Patterns Service — The Market Lion.
Detects classical chart patterns + advanced harmonic patterns on OHLCV data.
Exposes FastAPI endpoints, caches results in Redis.
"""
import asyncio
import logging
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as aioredis

logger = logging.getLogger("patterns-service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Patterns Service", version="1.0.0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/4")


# ─── Data Models ──────────────────────────────────────────────────────────────

class PatternType(str, Enum):
    # Classical
    HEAD_AND_SHOULDERS     = "HEAD_AND_SHOULDERS"
    INV_HEAD_AND_SHOULDERS = "INV_HEAD_AND_SHOULDERS"
    DOUBLE_TOP             = "DOUBLE_TOP"
    DOUBLE_BOTTOM          = "DOUBLE_BOTTOM"
    TRIPLE_TOP             = "TRIPLE_TOP"
    TRIPLE_BOTTOM          = "TRIPLE_BOTTOM"
    ASCENDING_TRIANGLE     = "ASCENDING_TRIANGLE"
    DESCENDING_TRIANGLE    = "DESCENDING_TRIANGLE"
    SYMMETRICAL_TRIANGLE   = "SYMMETRICAL_TRIANGLE"
    BULL_FLAG              = "BULL_FLAG"
    BEAR_FLAG              = "BEAR_FLAG"
    BULL_PENNANT           = "BULL_PENNANT"
    BEAR_PENNANT           = "BEAR_PENNANT"
    RISING_WEDGE           = "RISING_WEDGE"
    FALLING_WEDGE          = "FALLING_WEDGE"
    CUP_AND_HANDLE         = "CUP_AND_HANDLE"
    RECTANGLE_BULL         = "RECTANGLE_BULL"
    RECTANGLE_BEAR         = "RECTANGLE_BEAR"
    ROUNDING_BOTTOM        = "ROUNDING_BOTTOM"
    BUMP_AND_RUN           = "BUMP_AND_RUN"
    QUASIMODO              = "QUASIMODO"
    # Harmonic
    GARTLEY_BULL           = "GARTLEY_BULL"
    GARTLEY_BEAR           = "GARTLEY_BEAR"
    BAT_BULL               = "BAT_BULL"
    BAT_BEAR               = "BAT_BEAR"
    BUTTERFLY_BULL         = "BUTTERFLY_BULL"
    BUTTERFLY_BEAR         = "BUTTERFLY_BEAR"
    CRAB_BULL              = "CRAB_BULL"
    CRAB_BEAR              = "CRAB_BEAR"
    CYPHER_BULL            = "CYPHER_BULL"
    CYPHER_BEAR            = "CYPHER_BEAR"
    SHARK_BULL             = "SHARK_BULL"
    SHARK_BEAR             = "SHARK_BEAR"
    ABCD_BULL              = "ABCD_BULL"
    ABCD_BEAR              = "ABCD_BEAR"
    THREE_DRIVES_BULL      = "THREE_DRIVES_BULL"
    THREE_DRIVES_BEAR      = "THREE_DRIVES_BEAR"


class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class PatternResult:
    pattern: PatternType
    direction: Direction
    confidence: float          # 0-1
    strength: float            # 0-1
    entry_zone: Tuple[float, float]
    stop_loss: float
    target_1: float
    target_2: float
    completion_pct: float      # how complete the pattern is 0-1
    key_levels: Dict[str, float]
    bars_to_complete: int
    detected_at_bar: int


class OHLCVInput(BaseModel):
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: Optional[List[float]] = None


class PatternScanRequest(BaseModel):
    asset: str
    timeframe: str
    ohlcv: OHLCVInput
    scan_classical: bool = True
    scan_harmonic: bool = True
    min_confidence: float = 0.6


# ─── Pivot Detection ──────────────────────────────────────────────────────────

def find_pivots(high: np.ndarray, low: np.ndarray, left: int = 3, right: int = 3) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """Find swing highs and lows."""
    pivot_highs = []
    pivot_lows = []
    n = len(high)
    for i in range(left, n - right):
        if all(high[i] >= high[i-j] for j in range(1, left+1)) and \
           all(high[i] >= high[i+j] for j in range(1, right+1)):
            pivot_highs.append((i, high[i]))
        if all(low[i] <= low[i-j] for j in range(1, left+1)) and \
           all(low[i] <= low[i+j] for j in range(1, right+1)):
            pivot_lows.append((i, low[i]))
    return pivot_highs, pivot_lows


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b != 0 else default


# ─── Classical Chart Pattern Detectors ───────────────────────────────────────

def detect_head_and_shoulders(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float) -> List[PatternResult]:
    patterns = []
    pivot_highs, pivot_lows = find_pivots(high, low, left=3, right=3)
    if len(pivot_highs) < 3:
        return patterns

    # Look for H&S: left shoulder < head > right shoulder, shoulders approx equal
    for i in range(len(pivot_highs) - 2):
        ls_idx, ls_val = pivot_highs[i]
        h_idx, h_val = pivot_highs[i+1]
        rs_idx, rs_val = pivot_highs[i+2]

        if not (h_val > ls_val and h_val > rs_val):
            continue
        if abs(ls_val - rs_val) > atr_val * 2:
            continue
        if not (ls_idx < h_idx < rs_idx):
            continue

        # Neckline: connect troughs between shoulders
        neck_lows_between = [pl for pl in pivot_lows if ls_idx < pl[0] < rs_idx]
        if len(neck_lows_between) < 2:
            continue
        neckline_left = neck_lows_between[0][1]
        neckline_right = neck_lows_between[-1][1]
        neckline = (neckline_left + neckline_right) / 2

        # Pattern height
        height = h_val - neckline
        target = neckline - height
        sl = rs_val + atr_val * 0.5
        confidence = max(0.5, 1.0 - abs(ls_val - rs_val) / (atr_val * 2))

        patterns.append(PatternResult(
            pattern=PatternType.HEAD_AND_SHOULDERS,
            direction=Direction.BEARISH, confidence=confidence, strength=0.80,
            entry_zone=(neckline - atr_val * 0.2, neckline + atr_val * 0.2),
            stop_loss=sl, target_1=neckline - height * 0.5, target_2=target,
            completion_pct=1.0 if close[-1] < neckline else 0.85,
            key_levels={"left_shoulder": ls_val, "head": h_val, "right_shoulder": rs_val,
                        "neckline": neckline, "target": target},
            bars_to_complete=0, detected_at_bar=rs_idx,
        ))

    # Inverse H&S (bullish)
    pivot_lows_list = pivot_lows
    for i in range(len(pivot_lows_list) - 2):
        ls_idx, ls_val = pivot_lows_list[i]
        h_idx, h_val = pivot_lows_list[i+1]
        rs_idx, rs_val = pivot_lows_list[i+2]
        if not (h_val < ls_val and h_val < rs_val):
            continue
        if abs(ls_val - rs_val) > atr_val * 2:
            continue
        neck_highs = [ph for ph in pivot_highs if ls_idx < ph[0] < rs_idx]
        if len(neck_highs) < 1:
            continue
        neckline = sum(ph[1] for ph in neck_highs) / len(neck_highs)
        height = neckline - h_val
        target = neckline + height
        sl = rs_val - atr_val * 0.5
        confidence = max(0.5, 1.0 - abs(ls_val - rs_val) / (atr_val * 2))
        patterns.append(PatternResult(
            pattern=PatternType.INV_HEAD_AND_SHOULDERS,
            direction=Direction.BULLISH, confidence=confidence, strength=0.80,
            entry_zone=(neckline - atr_val * 0.2, neckline + atr_val * 0.2),
            stop_loss=sl, target_1=neckline + height * 0.5, target_2=target,
            completion_pct=1.0 if close[-1] > neckline else 0.85,
            key_levels={"left_shoulder": ls_val, "head": h_val, "right_shoulder": rs_val,
                        "neckline": neckline, "target": target},
            bars_to_complete=0, detected_at_bar=rs_idx,
        ))
    return patterns


def detect_double_tops_bottoms(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float) -> List[PatternResult]:
    patterns = []
    pivot_highs, pivot_lows = find_pivots(high, low)

    # Double Top
    for i in range(len(pivot_highs) - 1):
        t1_idx, t1_val = pivot_highs[i]
        t2_idx, t2_val = pivot_highs[i+1]
        if abs(t1_val - t2_val) > atr_val * 1.5:
            continue
        mid_lows = [pl for pl in pivot_lows if t1_idx < pl[0] < t2_idx]
        if not mid_lows:
            continue
        neckline = min(pl[1] for pl in mid_lows)
        height = ((t1_val + t2_val) / 2) - neckline
        target = neckline - height
        confidence = max(0.55, 1.0 - abs(t1_val - t2_val) / (atr_val * 2))
        patterns.append(PatternResult(
            pattern=PatternType.DOUBLE_TOP, direction=Direction.BEARISH,
            confidence=confidence, strength=0.75,
            entry_zone=(neckline - atr_val * 0.1, neckline + atr_val * 0.1),
            stop_loss=max(t1_val, t2_val) + atr_val * 0.3,
            target_1=neckline - height * 0.5, target_2=target,
            completion_pct=1.0 if close[-1] < neckline else 0.8,
            key_levels={"top1": t1_val, "top2": t2_val, "neckline": neckline},
            bars_to_complete=0, detected_at_bar=t2_idx,
        ))

    # Double Bottom
    for i in range(len(pivot_lows) - 1):
        b1_idx, b1_val = pivot_lows[i]
        b2_idx, b2_val = pivot_lows[i+1]
        if abs(b1_val - b2_val) > atr_val * 1.5:
            continue
        mid_highs = [ph for ph in pivot_highs if b1_idx < ph[0] < b2_idx]
        if not mid_highs:
            continue
        neckline = max(ph[1] for ph in mid_highs)
        height = neckline - ((b1_val + b2_val) / 2)
        target = neckline + height
        confidence = max(0.55, 1.0 - abs(b1_val - b2_val) / (atr_val * 2))
        patterns.append(PatternResult(
            pattern=PatternType.DOUBLE_BOTTOM, direction=Direction.BULLISH,
            confidence=confidence, strength=0.75,
            entry_zone=(neckline - atr_val * 0.1, neckline + atr_val * 0.1),
            stop_loss=min(b1_val, b2_val) - atr_val * 0.3,
            target_1=neckline + height * 0.5, target_2=target,
            completion_pct=1.0 if close[-1] > neckline else 0.8,
            key_levels={"bottom1": b1_val, "bottom2": b2_val, "neckline": neckline},
            bars_to_complete=0, detected_at_bar=b2_idx,
        ))
    return patterns


def detect_triangles_wedges(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float) -> List[PatternResult]:
    patterns = []
    n = len(close)
    lb = min(n, 40)
    if lb < 15:
        return patterns

    h = high[-lb:]
    l = low[-lb:]
    x = np.arange(lb)

    h_slope, h_intercept = np.polyfit(x, h, 1)
    l_slope, l_intercept = np.polyfit(x, l, 1)

    price = close[-1]
    upper_line = h_intercept + h_slope * (lb - 1)
    lower_line = l_intercept + l_slope * (lb - 1)
    width = upper_line - lower_line
    initial_width = (h_intercept + h_slope * 0) - (l_intercept + l_slope * 0)
    convergence = 1.0 - safe_div(width, initial_width)

    if convergence > 0.3:  # converging
        if abs(h_slope) < atr_val * 0.01 and l_slope > 0:
            # Ascending triangle: flat top, rising bottom
            target = upper_line + (upper_line - lower_line)
            patterns.append(PatternResult(
                pattern=PatternType.ASCENDING_TRIANGLE, direction=Direction.BULLISH,
                confidence=min(0.85, convergence), strength=0.72,
                entry_zone=(upper_line, upper_line + atr_val * 0.3),
                stop_loss=lower_line - atr_val * 0.2, target_1=upper_line + width * 0.5, target_2=target,
                completion_pct=convergence, key_levels={"resistance": upper_line, "support_line": lower_line},
                bars_to_complete=max(0, int((1 - convergence) * 10)), detected_at_bar=n - 1,
            ))
        elif abs(l_slope) < atr_val * 0.01 and h_slope < 0:
            # Descending triangle
            target = lower_line - (upper_line - lower_line)
            patterns.append(PatternResult(
                pattern=PatternType.DESCENDING_TRIANGLE, direction=Direction.BEARISH,
                confidence=min(0.85, convergence), strength=0.72,
                entry_zone=(lower_line - atr_val * 0.3, lower_line),
                stop_loss=upper_line + atr_val * 0.2, target_1=lower_line - width * 0.5, target_2=target,
                completion_pct=convergence, key_levels={"support": lower_line, "resistance_line": upper_line},
                bars_to_complete=max(0, int((1 - convergence) * 10)), detected_at_bar=n - 1,
            ))
        elif h_slope > 0 and l_slope > 0 and h_slope < l_slope:
            # Rising wedge — bearish
            patterns.append(PatternResult(
                pattern=PatternType.RISING_WEDGE, direction=Direction.BEARISH,
                confidence=min(0.80, convergence), strength=0.70,
                entry_zone=(lower_line - atr_val * 0.2, lower_line + atr_val * 0.1),
                stop_loss=upper_line + atr_val * 0.3,
                target_1=lower_line - width, target_2=lower_line - width * 1.5,
                completion_pct=convergence, key_levels={"upper": upper_line, "lower": lower_line},
                bars_to_complete=max(0, int((1 - convergence) * 8)), detected_at_bar=n - 1,
            ))
        elif h_slope < 0 and l_slope < 0 and h_slope > l_slope:
            # Falling wedge — bullish
            patterns.append(PatternResult(
                pattern=PatternType.FALLING_WEDGE, direction=Direction.BULLISH,
                confidence=min(0.80, convergence), strength=0.70,
                entry_zone=(upper_line - atr_val * 0.1, upper_line + atr_val * 0.2),
                stop_loss=lower_line - atr_val * 0.3,
                target_1=upper_line + width, target_2=upper_line + width * 1.5,
                completion_pct=convergence, key_levels={"upper": upper_line, "lower": lower_line},
                bars_to_complete=max(0, int((1 - convergence) * 8)), detected_at_bar=n - 1,
            ))
        else:
            # Symmetrical triangle
            direction = Direction.BULLISH if close[-1] > close[-lb] else Direction.BEARISH
            patterns.append(PatternResult(
                pattern=PatternType.SYMMETRICAL_TRIANGLE, direction=direction,
                confidence=min(0.70, convergence), strength=0.65,
                entry_zone=(lower_line, upper_line),
                stop_loss=lower_line - atr_val if direction == Direction.BULLISH else upper_line + atr_val,
                target_1=(upper_line + width) if direction == Direction.BULLISH else (lower_line - width),
                target_2=(upper_line + initial_width) if direction == Direction.BULLISH else (lower_line - initial_width),
                completion_pct=convergence, key_levels={"upper": upper_line, "lower": lower_line},
                bars_to_complete=max(0, int((1 - convergence) * 8)), detected_at_bar=n - 1,
            ))
    return patterns


def detect_flags_pennants(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float) -> List[PatternResult]:
    patterns = []
    n = len(close)
    if n < 15:
        return patterns

    # Flagpole: strong 5-10 bar move
    for pole_len in [5, 8, 10]:
        if n < pole_len + 5:
            continue
        pole_start = close[-pole_len - 5]
        pole_end = close[-5]
        pole_move = pole_end - pole_start
        if abs(pole_move) < atr_val * pole_len * 0.5:
            continue

        # Flag: tight consolidation (last 5 bars)
        flag_range = max(high[-5:]) - min(low[-5:])
        consolidation = flag_range < atr_val * 2.0

        if not consolidation:
            continue

        if pole_move > 0:
            # Bull flag
            target = close[-1] + abs(pole_move)
            patterns.append(PatternResult(
                pattern=PatternType.BULL_FLAG, direction=Direction.BULLISH,
                confidence=0.78, strength=0.75,
                entry_zone=(max(high[-5:]), max(high[-5:]) + atr_val * 0.2),
                stop_loss=min(low[-5:]) - atr_val * 0.2,
                target_1=close[-1] + abs(pole_move) * 0.5, target_2=target,
                completion_pct=0.9,
                key_levels={"pole_start": pole_start, "pole_end": pole_end,
                            "flag_high": max(high[-5:]), "flag_low": min(low[-5:])},
                bars_to_complete=1, detected_at_bar=n - 1,
            ))
        else:
            # Bear flag
            target = close[-1] - abs(pole_move)
            patterns.append(PatternResult(
                pattern=PatternType.BEAR_FLAG, direction=Direction.BEARISH,
                confidence=0.78, strength=0.75,
                entry_zone=(min(low[-5:]) - atr_val * 0.2, min(low[-5:])),
                stop_loss=max(high[-5:]) + atr_val * 0.2,
                target_1=close[-1] - abs(pole_move) * 0.5, target_2=target,
                completion_pct=0.9,
                key_levels={"pole_start": pole_start, "pole_end": pole_end,
                            "flag_high": max(high[-5:]), "flag_low": min(low[-5:])},
                bars_to_complete=1, detected_at_bar=n - 1,
            ))
    return patterns


def detect_cup_and_handle(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float) -> List[PatternResult]:
    patterns = []
    n = len(close)
    if n < 30:
        return patterns

    # Cup: U-shape over 20-30 bars
    lb = min(n, 40)
    segment = close[-lb:]
    cup_left = segment[0]
    cup_right = segment[-10]  # before handle
    cup_bottom = min(segment[:-10])
    cup_depth = ((cup_left + cup_right) / 2) - cup_bottom

    if cup_depth < atr_val * 3:
        return patterns

    # Symmetry check
    left_drop = cup_left - cup_bottom
    right_rise = cup_right - cup_bottom
    symmetry = min(left_drop, right_rise) / max(left_drop, right_rise) if max(left_drop, right_rise) > 0 else 0

    if symmetry < 0.4:
        return patterns

    # Handle: small pullback after cup right rim
    handle_high = max(high[-8:-1])
    handle_low = min(low[-8:-1])
    handle_depth_ratio = safe_div(cup_right - handle_low, cup_depth)

    if 0.3 < handle_depth_ratio < 0.6:
        target = cup_right + cup_depth
        patterns.append(PatternResult(
            pattern=PatternType.CUP_AND_HANDLE, direction=Direction.BULLISH,
            confidence=min(0.85, symmetry * 0.7 + 0.3), strength=0.78,
            entry_zone=(cup_right, cup_right + atr_val * 0.3),
            stop_loss=handle_low - atr_val * 0.2,
            target_1=cup_right + cup_depth * 0.5, target_2=target,
            completion_pct=0.9,
            key_levels={"cup_left": cup_left, "cup_bottom": cup_bottom,
                        "cup_right": cup_right, "handle_low": handle_low},
            bars_to_complete=1, detected_at_bar=n - 1,
        ))
    return patterns


# ─── Harmonic Pattern Detectors ──────────────────────────────────────────────

HARMONIC_RATIOS = {
    "GARTLEY":   {"XB": (0.618, 0.618), "AC": (0.382, 0.886), "BD": (1.27, 1.618), "XD": (0.786, 0.786)},
    "BAT":       {"XB": (0.382, 0.500), "AC": (0.382, 0.886), "BD": (1.618, 2.618), "XD": (0.886, 0.886)},
    "BUTTERFLY": {"XB": (0.786, 0.786), "AC": (0.382, 0.886), "BD": (1.618, 2.618), "XD": (1.272, 1.272)},
    "CRAB":      {"XB": (0.382, 0.618), "AC": (0.382, 0.886), "BD": (2.240, 3.618), "XD": (1.618, 1.618)},
    "CYPHER":    {"XB": (0.382, 0.618), "AC": (1.130, 1.414), "BD": (1.272, 2.000), "XD": (0.786, 0.786)},
    "SHARK":     {"XB": (0.446, 0.618), "AC": (1.130, 1.618), "BD": (1.618, 2.240), "XD": (0.886, 1.130)},
}

TOL = 0.06  # ratio tolerance


def ratio_ok(ratio: float, low: float, high: float) -> bool:
    return low * (1 - TOL) <= ratio <= high * (1 + TOL)


def detect_harmonic(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float) -> List[PatternResult]:
    patterns = []
    pivot_highs, pivot_lows = find_pivots(high, low, left=2, right=2)

    # Need at least 5 pivots for XABCD
    all_pivots = sorted(pivot_highs + pivot_lows, key=lambda p: p[0])
    if len(all_pivots) < 5:
        return patterns

    # Check last 5 pivots
    for i in range(max(0, len(all_pivots) - 8), len(all_pivots) - 4):
        pts = all_pivots[i:i+5]
        X, A, B, C, D = pts

        XA = A[1] - X[1]
        AB = B[1] - A[1]
        BC = C[1] - B[1]
        CD = D[1] - C[1]

        if abs(XA) < atr_val * 2 or abs(AB) < atr_val:
            continue

        XB_ratio = safe_div(abs(AB), abs(XA))
        AC_ratio = safe_div(abs(BC), abs(AB))
        BD_ratio = safe_div(abs(CD), abs(BC)) if abs(BC) > 0 else 0
        XD_ratio = safe_div(abs(D[1] - X[1]), abs(XA))

        is_bull = XA < 0  # X is above A (bullish setup: price declined XA then forms pattern)

        for pattern_name, ratios in HARMONIC_RATIOS.items():
            xb_ok = ratio_ok(XB_ratio, *ratios["XB"])
            ac_ok = ratio_ok(AC_ratio, *ratios["AC"])
            bd_ok = ratio_ok(BD_ratio, *ratios["BD"])
            xd_ok = ratio_ok(XD_ratio, *ratios["XD"])

            if xb_ok and ac_ok and bd_ok and xd_ok:
                match_score = sum([xb_ok, ac_ok, bd_ok, xd_ok]) / 4
                conf = 0.60 + match_score * 0.35

                if is_bull:
                    pt = getattr(PatternType, f"{pattern_name}_BULL", None)
                    direction = Direction.BULLISH
                    target1 = D[1] + abs(XA) * 0.382
                    target2 = D[1] + abs(XA) * 0.618
                    sl = D[1] - atr_val * 1.5
                else:
                    pt = getattr(PatternType, f"{pattern_name}_BEAR", None)
                    direction = Direction.BEARISH
                    target1 = D[1] - abs(XA) * 0.382
                    target2 = D[1] - abs(XA) * 0.618
                    sl = D[1] + atr_val * 1.5

                if pt is None:
                    continue

                patterns.append(PatternResult(
                    pattern=pt, direction=direction,
                    confidence=round(conf, 3), strength=0.80,
                    entry_zone=(D[1] - atr_val * 0.3, D[1] + atr_val * 0.3),
                    stop_loss=sl, target_1=target1, target_2=target2,
                    completion_pct=1.0,
                    key_levels={"X": X[1], "A": A[1], "B": B[1], "C": C[1], "D": D[1],
                                "XB": round(XB_ratio, 3), "AC": round(AC_ratio, 3),
                                "BD": round(BD_ratio, 3), "XD": round(XD_ratio, 3)},
                    bars_to_complete=0, detected_at_bar=D[0],
                ))
    return patterns


def detect_abcd(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float) -> List[PatternResult]:
    patterns = []
    pivot_highs, pivot_lows = find_pivots(high, low, left=2, right=2)
    all_pivots = sorted(pivot_highs + pivot_lows, key=lambda p: p[0])
    if len(all_pivots) < 4:
        return patterns

    for i in range(max(0, len(all_pivots) - 6), len(all_pivots) - 3):
        A, B, C, D = all_pivots[i:i+4]
        AB = abs(B[1] - A[1])
        BC = abs(C[1] - B[1])
        CD = abs(D[1] - C[1])
        if AB < atr_val or BC < atr_val * 0.3:
            continue
        BC_AB = safe_div(BC, AB)
        CD_BC = safe_div(CD, BC)

        if ratio_ok(BC_AB, 0.382, 0.886) and ratio_ok(CD_BC, 1.13, 1.618):
            is_bull = A[1] > B[1]  # A to B decline = bullish ABCD
            direction = Direction.BULLISH if is_bull else Direction.BEARISH
            pt = PatternType.ABCD_BULL if is_bull else PatternType.ABCD_BEAR
            target = D[1] + (AB if is_bull else -AB)
            sl = D[1] - atr_val * 1.2 if is_bull else D[1] + atr_val * 1.2
            patterns.append(PatternResult(
                pattern=pt, direction=direction, confidence=0.72, strength=0.70,
                entry_zone=(D[1] - atr_val * 0.2, D[1] + atr_val * 0.2),
                stop_loss=sl, target_1=D[1] + AB * 0.618 * (1 if is_bull else -1), target_2=target,
                completion_pct=1.0,
                key_levels={"A": A[1], "B": B[1], "C": C[1], "D": D[1],
                            "BC_AB": round(BC_AB, 3), "CD_BC": round(CD_BC, 3)},
                bars_to_complete=0, detected_at_bar=D[0],
            ))
    return patterns


# ─── ATR helper ───────────────────────────────────────────────────────────────

def calc_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
    if len(close) < period + 1:
        return float(np.mean(high - low))
    tr = np.maximum(high[1:] - low[1:],
         np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
    atr_vals = np.zeros(len(close))
    atr_vals[period] = np.mean(tr[:period])
    for i in range(period + 1, len(close)):
        atr_vals[i] = (atr_vals[i-1] * (period - 1) + tr[i-1]) / period
    return float(np.nanmean(atr_vals[-20:]))


# ─── Master Scanner ───────────────────────────────────────────────────────────

def scan_all_patterns(
    high: np.ndarray, low: np.ndarray, close: np.ndarray,
    scan_classical: bool = True, scan_harmonic: bool = True,
    min_confidence: float = 0.6,
) -> List[PatternResult]:
    atr_val = calc_atr(high, low, close)
    all_patterns: List[PatternResult] = []

    if scan_classical:
        all_patterns.extend(detect_head_and_shoulders(high, low, close, atr_val))
        all_patterns.extend(detect_double_tops_bottoms(high, low, close, atr_val))
        all_patterns.extend(detect_triangles_wedges(high, low, close, atr_val))
        all_patterns.extend(detect_flags_pennants(high, low, close, atr_val))
        all_patterns.extend(detect_cup_and_handle(high, low, close, atr_val))

    if scan_harmonic:
        all_patterns.extend(detect_harmonic(high, low, close, atr_val))
        all_patterns.extend(detect_abcd(high, low, close, atr_val))

    # Filter by confidence and deduplicate by pattern type
    filtered = [p for p in all_patterns if p.confidence >= min_confidence]
    seen = set()
    deduped = []
    for p in sorted(filtered, key=lambda x: -x.confidence):
        if p.pattern not in seen:
            seen.add(p.pattern)
            deduped.append(p)

    return deduped


def aggregate_pattern_vote(patterns: List[PatternResult]) -> Dict[str, Any]:
    if not patterns:
        return {"vote": "NEUTRAL", "score": 0.0, "confidence": 0.5}
    bull_score = sum(p.confidence * p.strength for p in patterns if p.direction == Direction.BULLISH)
    bear_score = sum(p.confidence * p.strength for p in patterns if p.direction == Direction.BEARISH)
    total = bull_score + bear_score + 1e-10
    net = (bull_score - bear_score) / total
    vote = "BUY" if net > 0.2 else ("SELL" if net < -0.2 else "NEUTRAL")
    return {
        "vote": vote, "score": round(net, 4),
        "confidence": round(max(bull_score, bear_score) / len(patterns), 4),
        "bull_patterns": [p.pattern for p in patterns if p.direction == Direction.BULLISH],
        "bear_patterns": [p.pattern for p in patterns if p.direction == Direction.BEARISH],
    }


# ─── Redis ────────────────────────────────────────────────────────────────────

_redis: Optional[aioredis.Redis] = None


async def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        except Exception:
            pass
    return _redis


# ─── FastAPI Endpoints ────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "patterns-service"}


@app.post("/scan")
async def scan_patterns(req: PatternScanRequest):
    high = np.array(req.ohlcv.high)
    low = np.array(req.ohlcv.low)
    close = np.array(req.ohlcv.close)

    if len(close) < 15:
        raise HTTPException(400, "Need at least 15 bars")

    cache_key = f"patterns:{req.asset}:{req.timeframe}"
    redis = await get_redis()
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

    patterns = scan_all_patterns(high, low, close, req.scan_classical, req.scan_harmonic, req.min_confidence)
    vote = aggregate_pattern_vote(patterns)

    result = {
        "asset": req.asset.upper(),
        "timeframe": req.timeframe.upper(),
        "patterns_found": len(patterns),
        "vote": vote,
        "patterns": [
            {
                "pattern": p.pattern, "direction": p.direction,
                "confidence": round(p.confidence, 4), "strength": round(p.strength, 4),
                "entry_zone": list(p.entry_zone),
                "stop_loss": round(p.stop_loss, 5),
                "target_1": round(p.target_1, 5), "target_2": round(p.target_2, 5),
                "completion_pct": p.completion_pct,
                "key_levels": {k: round(v, 5) for k, v in p.key_levels.items()},
                "bars_to_complete": p.bars_to_complete,
            }
            for p in patterns
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if redis:
        await redis.setex(cache_key, 120, json.dumps(result))

    return result


@app.post("/scan/harmonic")
async def scan_harmonic_only(req: PatternScanRequest):
    req.scan_classical = False
    req.scan_harmonic = True
    return await scan_patterns(req)


@app.post("/scan/classical")
async def scan_classical_only(req: PatternScanRequest):
    req.scan_classical = True
    req.scan_harmonic = False
    return await scan_patterns(req)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pattern_engine:app", host="0.0.0.0", port=8009, reload=False)
