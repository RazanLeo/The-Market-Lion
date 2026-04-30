"""Market Lion — Elliott Wave Counter + Gann Analysis + Harmonic Patterns.
Elliott Wave: identifies current wave position (1-5, A-B-C) from swing pivots.
Gann: Square of 9 price levels + Gann Fan angles.
Harmonics: Gartley, Bat, Butterfly, Crab, Shark, Cypher, AB=CD.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


# ──────────────────────────────────────────────
# Fibonacci ratios used across all systems
# ──────────────────────────────────────────────
FIB_RATIOS = {
    "0.236": 0.236, "0.382": 0.382, "0.500": 0.500, "0.618": 0.618,
    "0.786": 0.786, "1.000": 1.000, "1.272": 1.272, "1.414": 1.414,
    "1.618": 1.618, "2.000": 2.000, "2.618": 2.618,
}


def fib_ratio_match(ratio: float, target: float, tolerance: float = 0.03) -> bool:
    return abs(ratio - target) <= tolerance


# ──────────────────────────────────────────────
# Swing Pivot Detection
# ──────────────────────────────────────────────
def find_pivots(highs: np.ndarray, lows: np.ndarray, window: int = 5) -> tuple[list, list]:
    """Returns (swing_highs, swing_lows) as (index, price) tuples."""
    swing_highs = []
    swing_lows = []
    n = len(highs)
    for i in range(window, n - window):
        if highs[i] == max(highs[i - window:i + window + 1]):
            swing_highs.append((i, float(highs[i])))
        if lows[i] == min(lows[i - window:i + window + 1]):
            swing_lows.append((i, float(lows[i])))
    return swing_highs, swing_lows


def zigzag(highs: np.ndarray, lows: np.ndarray, threshold: float = 0.005) -> list[tuple]:
    """Simple ZigZag pivot points above threshold% move."""
    pivots = []
    direction = 0
    last_high = float(highs[0])
    last_low = float(lows[0])
    last_idx = 0

    for i in range(1, len(highs)):
        h, l = float(highs[i]), float(lows[i])
        if direction <= 0:
            if h > last_high * (1 + threshold):
                if direction == -1:
                    pivots.append((last_idx, last_low, "low"))
                last_high = h
                last_idx = i
                direction = 1
            elif l < last_low:
                last_low = l
                last_idx = i
        else:
            if l < last_low * (1 - threshold):
                if direction == 1:
                    pivots.append((last_idx, last_high, "high"))
                last_low = l
                last_idx = i
                direction = -1
            elif h > last_high:
                last_high = h
                last_idx = i

    return pivots


# ──────────────────────────────────────────────
# Elliott Wave
# ──────────────────────────────────────────────
@dataclass
class ElliottWaveResult:
    wave_count: str          # e.g. "Wave 3", "Wave C", "Unclear"
    direction: str           # BUY / SELL / NEUTRAL
    confidence: float
    next_target: Optional[float]
    invalidation: Optional[float]
    details: dict


def analyze_elliott_wave(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> ElliottWaveResult:
    """Simplified Elliott Wave counter using ZigZag pivots."""
    if len(closes) < 50:
        return ElliottWaveResult("Insufficient data", "NEUTRAL", 0.0, None, None, {})

    current_price = float(closes[-1])
    pivots = zigzag(highs, lows, threshold=0.003)

    if len(pivots) < 5:
        return ElliottWaveResult("Unclear", "NEUTRAL", 0.3, None, None, {"pivots": len(pivots)})

    # Extract last 5+ pivots for wave counting
    pts = pivots[-8:]  # last 8 pivot points
    prices = [p[1] for p in pts]
    types = [p[2] for p in pts]

    result = {
        "pivot_count": len(pts),
        "current_price": current_price,
    }

    # Check for 5-wave impulse pattern
    if len(pts) >= 5 and types[0] == "low":
        # Bullish impulse: low-high-low-high-low-high-low-high-low-high (waves 1-5)
        w = prices[:5]
        w1_end = w[1] - w[0]  # wave 1 length
        w3_end = w[3] - w[2]  # wave 3 length
        w5_proj = w[4] + w1_end  # wave 5 target

        # Wave 3 should not be shortest
        if w3_end > w1_end * 0.618:
            # Currently likely in wave 5 or completed 5 waves
            if current_price > w[4] and current_price < w5_proj:
                return ElliottWaveResult(
                    wave_count="Wave 5", direction="BUY", confidence=0.65,
                    next_target=round(w5_proj, 5), invalidation=round(float(w[4]) * 0.995, 5),
                    details={**result, "wave5_target": round(w5_proj, 5)}
                )
            elif current_price > w5_proj * 0.99:
                # Completed 5 waves — expect correction (A-B-C)
                correction_target = w[0] + (w5_proj - w[0]) * 0.382
                return ElliottWaveResult(
                    wave_count="Wave A (Correction)", direction="SELL", confidence=0.6,
                    next_target=round(correction_target, 5), invalidation=round(w5_proj * 1.01, 5),
                    details={**result, "correction_target": round(correction_target, 5)}
                )

    # Check for corrective ABC
    if len(pts) >= 3 and types[-3] == "high":
        a_move = prices[-2] - prices[-3]  # negative = correction
        c_proj = prices[-1] - a_move * 1.0  # C = A

        if current_price < prices[-3] and current_price > prices[-2]:
            return ElliottWaveResult(
                wave_count="Wave B (Bounce)", direction="SELL", confidence=0.55,
                next_target=round(float(prices[-3]) * 0.998, 5),
                invalidation=round(float(prices[-3]) * 1.005, 5),
                details={**result, "c_target": round(c_proj, 5)}
            )

    # Wave 3 detection (strongest move)
    if len(pts) >= 4:
        moves = [abs(prices[i+1] - prices[i]) for i in range(len(prices)-1)]
        if moves:
            max_move_idx = moves.index(max(moves))
            if max_move_idx in range(1, len(moves)-1):
                direction = "BUY" if prices[max_move_idx+1] > prices[max_move_idx] else "SELL"
                return ElliottWaveResult(
                    wave_count="Wave 3 (Extended)", direction=direction, confidence=0.7,
                    next_target=None, invalidation=None,
                    details={**result, "max_move": round(max(moves), 5)}
                )

    return ElliottWaveResult("Unclear", "NEUTRAL", 0.3, None, None, result)


# ──────────────────────────────────────────────
# Gann Analysis
# ──────────────────────────────────────────────
def gann_square_of_9(price: float) -> dict:
    """Gann Square of 9 key levels."""
    sqrt_price = np.sqrt(price)
    levels = {}
    for i in range(-4, 5):
        if i == 0:
            continue
        level = (sqrt_price + i * 0.125) ** 2
        levels[f"G{i:+d}"] = round(level, 5)
    return levels


def gann_fan_levels(swing_low: float, swing_high: float, swing_time_bars: int) -> dict:
    """Gann Fan angles (1×1, 1×2, 2×1, etc.) projected from swing."""
    price_range = swing_high - swing_low
    price_per_bar = price_range / max(swing_time_bars, 1)
    fans = {}
    angles = {
        "1x8": 1/8, "1x4": 1/4, "1x3": 1/3, "1x2": 1/2,
        "1x1": 1.0, "2x1": 2.0, "3x1": 3.0, "4x1": 4.0, "8x1": 8.0,
    }
    for name, ratio in angles.items():
        fans[name] = round(swing_low + price_per_bar * ratio * swing_time_bars, 5)
    return fans


def analyze_gann(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> dict:
    """Returns Gann S9 levels and fan projections."""
    current_price = float(closes[-1])
    recent_high = float(np.max(highs[-50:]))
    recent_low = float(np.min(lows[-50:]))
    high_idx = int(np.argmax(highs[-50:]))
    low_idx = int(np.argmin(lows[-50:]))

    s9 = gann_square_of_9(current_price)

    # Find nearest resistance and support levels
    above = {k: v for k, v in s9.items() if v > current_price}
    below = {k: v for k, v in s9.items() if v < current_price}

    resistance = min(above.values()) if above else current_price * 1.005
    support = max(below.values()) if below else current_price * 0.995

    fan = gann_fan_levels(recent_low, recent_high, abs(high_idx - low_idx) or 1)

    vote = "NEUTRAL"
    confidence = 0.5
    if current_price > resistance * 0.999:
        vote = "BUY"
        confidence = 0.6
    elif current_price < support * 1.001:
        vote = "SELL"
        confidence = 0.6

    return {
        "vote": vote,
        "confidence": confidence,
        "current_price": current_price,
        "gann_resistance": resistance,
        "gann_support": support,
        "square_of_9": s9,
        "gann_fans": fan,
    }


# ──────────────────────────────────────────────
# Harmonic Patterns
# ──────────────────────────────────────────────
HARMONIC_RATIOS = {
    "Gartley":   {"XA_B": 0.618, "AB_C": (0.382, 0.886), "BC_D": (1.272, 1.618), "XA_D": 0.786},
    "Bat":       {"XA_B": (0.382, 0.500), "AB_C": (0.382, 0.886), "BC_D": (1.618, 2.618), "XA_D": 0.886},
    "Butterfly": {"XA_B": 0.786, "AB_C": (0.382, 0.886), "BC_D": (1.618, 2.618), "XA_D": (1.272, 1.618)},
    "Crab":      {"XA_B": (0.382, 0.618), "AB_C": (0.382, 0.886), "BC_D": (2.618, 3.618), "XA_D": 1.618},
    "Shark":     {"XA_B": (0.446, 0.618), "AB_C": (1.130, 1.618), "BC_D": (0.886, 1.130), "XA_D": 0.886},
    "Cypher":    {"XA_B": (0.382, 0.618), "AB_C": (1.272, 1.414), "BC_D": (0.786,), "XA_D": 0.786},
    "ABCD":      {"AB_BC": 0.618, "BC_CD": 1.272},
}


def check_ratio(value: float, target, tolerance: float = 0.05) -> bool:
    if isinstance(target, tuple):
        lo, hi = target[0], target[-1]
        return lo * (1 - tolerance) <= value <= hi * (1 + tolerance)
    return fib_ratio_match(value, target, tolerance)


@dataclass
class HarmonicResult:
    pattern: str
    direction: str  # BUY / SELL
    confidence: float
    completion_price: float
    stop_loss: float
    target_1: float
    target_2: float
    points: dict


def scan_harmonic_patterns(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> list[HarmonicResult]:
    """Scan for harmonic patterns using last pivot points."""
    results = []
    pivots = zigzag(highs, lows, threshold=0.004)

    if len(pivots) < 5:
        return results

    # Check last 5 pivots as X-A-B-C-D
    for start in range(max(0, len(pivots) - 6), len(pivots) - 4):
        pts = pivots[start:start + 5]
        X, A, B, C, D = [p[1] for p in pts]

        # Determine if bullish (X is high) or bearish (X is low)
        for is_bullish_pattern in [True, False]:
            if is_bullish_pattern:
                XA = A - X  # negative for bearish X
                if XA <= 0:
                    continue
            else:
                XA = X - A
                if XA <= 0:
                    continue

            AB = abs(B - A)
            BC = abs(C - B)
            CD = abs(D - C)
            XA_B = AB / XA if XA else 0
            AB_C = BC / AB if AB else 0
            BC_D = CD / BC if BC else 0
            XA_D = abs(D - X) / XA if XA else 0

            for pattern_name, ratios in HARMONIC_RATIOS.items():
                if pattern_name == "ABCD":
                    if check_ratio(XA_B, ratios["AB_BC"]) and check_ratio(AB_C, ratios["BC_CD"]):
                        direction = "BUY" if is_bullish_pattern else "SELL"
                        sl = D * (0.995 if direction == "BUY" else 1.005)
                        tp1 = D + (A - D) * 0.382
                        tp2 = D + (A - D) * 0.618
                        results.append(HarmonicResult(
                            pattern="AB=CD", direction=direction, confidence=0.65,
                            completion_price=round(D, 5), stop_loss=round(sl, 5),
                            target_1=round(tp1, 5), target_2=round(tp2, 5),
                            points={"X": round(X,5), "A": round(A,5), "B": round(B,5), "C": round(C,5), "D": round(D,5)}
                        ))
                    continue

                passes = True
                if "XA_B" in ratios and not check_ratio(XA_B, ratios["XA_B"]):
                    passes = False
                if "AB_C" in ratios and not check_ratio(AB_C, ratios["AB_C"]):
                    passes = False
                if "BC_D" in ratios and not check_ratio(BC_D, ratios["BC_D"]):
                    passes = False
                if "XA_D" in ratios and not check_ratio(XA_D, ratios["XA_D"]):
                    passes = False

                if passes:
                    direction = "BUY" if is_bullish_pattern else "SELL"
                    sl_pct = 0.993 if direction == "BUY" else 1.007
                    tp1_pct = 0.382
                    tp2_pct = 0.618
                    tp1 = D + (A - D) * tp1_pct
                    tp2 = D + (A - D) * tp2_pct
                    results.append(HarmonicResult(
                        pattern=pattern_name, direction=direction, confidence=0.72,
                        completion_price=round(D, 5), stop_loss=round(D * sl_pct, 5),
                        target_1=round(tp1, 5), target_2=round(tp2, 5),
                        points={"X": round(X,5), "A": round(A,5), "B": round(B,5), "C": round(C,5), "D": round(D,5)}
                    ))

    return results[:3]  # return best 3


def analyze_harmonics_vote(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> dict:
    """Aggregate harmonic analysis into a vote."""
    patterns = scan_harmonic_patterns(highs, lows, closes)
    if not patterns:
        return {"vote": "NEUTRAL", "confidence": 0.3, "patterns": []}

    buy_conf = sum(p.confidence for p in patterns if p.direction == "BUY")
    sell_conf = sum(p.confidence for p in patterns if p.direction == "SELL")

    if buy_conf > sell_conf:
        vote, confidence = "BUY", buy_conf / len(patterns)
    elif sell_conf > buy_conf:
        vote, confidence = "SELL", sell_conf / len(patterns)
    else:
        vote, confidence = "NEUTRAL", 0.4

    return {
        "vote": vote,
        "confidence": round(confidence, 3),
        "patterns": [{"name": p.pattern, "direction": p.direction, "confidence": p.confidence,
                      "completion": p.completion_price, "sl": p.stop_loss,
                      "tp1": p.target_1, "tp2": p.target_2} for p in patterns],
    }
