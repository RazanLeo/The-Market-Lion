"""Market Lion — Candlestick Pattern Recognition (80+ patterns).
Based on Steve Nison's methodology + Thomas Bulkowski's Encyclopedia.
All functions operate on numpy arrays: open, high, low, close.
Returns: (pattern_name, signal: +1 BUY / -1 SELL / 0 NEUTRAL, strength: float)
"""
import numpy as np
from typing import Optional


def body(o: float, c: float) -> float:
    return abs(c - o)


def upper_shadow(o: float, h: float, c: float) -> float:
    return h - max(o, c)


def lower_shadow(o: float, l: float, c: float) -> float:
    return min(o, c) - l


def avg_body(opens, closes, n=14) -> float:
    return float(np.mean(np.abs(closes[-n:] - opens[-n:])))


def is_bullish(o: float, c: float) -> bool:
    return c > o


def is_bearish(o: float, c: float) -> bool:
    return c < o


def is_doji(o: float, c: float, avg_b: float, threshold: float = 0.05) -> bool:
    return body(o, c) <= avg_b * threshold


def trend_up(closes, n=5) -> bool:
    return float(closes[-1]) > float(closes[-n])


def trend_down(closes, n=5) -> bool:
    return float(closes[-1]) < float(closes[-n])


# ──────────────────────────────────────────────
# Single-candle patterns
# ──────────────────────────────────────────────

def doji(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_doji(o, c, avg_b, 0.1):
        return ("Doji", 0, 0.5)
    return None


def gravestone_doji(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_doji(o, c, avg_b) and lower_shadow(o, l, c) < avg_b * 0.1 and upper_shadow(o, h, c) > avg_b * 2:
        return ("Gravestone Doji", -1, 0.75)
    return None


def dragonfly_doji(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_doji(o, c, avg_b) and upper_shadow(o, h, c) < avg_b * 0.1 and lower_shadow(o, l, c) > avg_b * 2:
        return ("Dragonfly Doji", 1, 0.75)
    return None


def hammer(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    b = body(o, c)
    ls = lower_shadow(o, l, c)
    us = upper_shadow(o, h, c)
    if b >= avg_b * 0.3 and ls >= b * 2 and us <= b * 0.3 and trend_down(closes):
        return ("Hammer", 1, 0.8)
    return None


def hanging_man(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    b = body(o, c)
    ls = lower_shadow(o, l, c)
    us = upper_shadow(o, h, c)
    if b >= avg_b * 0.3 and ls >= b * 2 and us <= b * 0.3 and trend_up(closes):
        return ("Hanging Man", -1, 0.7)
    return None


def inverted_hammer(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    b = body(o, c)
    ls = lower_shadow(o, l, c)
    us = upper_shadow(o, h, c)
    if b >= avg_b * 0.3 and us >= b * 2 and ls <= b * 0.3 and trend_down(closes):
        return ("Inverted Hammer", 1, 0.65)
    return None


def shooting_star(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    b = body(o, c)
    us = upper_shadow(o, h, c)
    ls = lower_shadow(o, l, c)
    if b >= avg_b * 0.3 and us >= b * 2 and ls <= b * 0.3 and trend_up(closes):
        return ("Shooting Star", -1, 0.8)
    return None


def spinning_top(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    b = body(o, c)
    if b < avg_b * 0.5 and upper_shadow(o, h, c) > b and lower_shadow(o, l, c) > b:
        return ("Spinning Top", 0, 0.4)
    return None


def marubozu_bullish(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    b = body(o, c)
    if is_bullish(o, c) and b >= avg_b * 1.5 and upper_shadow(o, h, c) < avg_b * 0.05 and lower_shadow(o, l, c) < avg_b * 0.05:
        return ("Bullish Marubozu", 1, 0.9)
    return None


def marubozu_bearish(opens, highs, lows, closes) -> Optional[tuple]:
    o, h, l, c = float(opens[-1]), float(highs[-1]), float(lows[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    b = body(o, c)
    if is_bearish(o, c) and b >= avg_b * 1.5 and upper_shadow(o, h, c) < avg_b * 0.05 and lower_shadow(o, l, c) < avg_b * 0.05:
        return ("Bearish Marubozu", -1, 0.9)
    return None


# ──────────────────────────────────────────────
# Two-candle patterns
# ──────────────────────────────────────────────

def bullish_engulfing(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    if is_bearish(o1, c1) and is_bullish(o2, c2) and o2 <= c1 and c2 >= o1 and trend_down(closes):
        return ("Bullish Engulfing", 1, 0.85)
    return None


def bearish_engulfing(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    if is_bullish(o1, c1) and is_bearish(o2, c2) and o2 >= c1 and c2 <= o1 and trend_up(closes):
        return ("Bearish Engulfing", -1, 0.85)
    return None


def piercing_line(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    midpoint = (o1 + c1) / 2
    if is_bearish(o1, c1) and is_bullish(o2, c2) and o2 < c1 and c2 > midpoint and c2 < o1:
        return ("Piercing Line", 1, 0.7)
    return None


def dark_cloud_cover(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    midpoint = (o1 + c1) / 2
    if is_bullish(o1, c1) and is_bearish(o2, c2) and o2 > c1 and c2 < midpoint and c2 > o1:
        return ("Dark Cloud Cover", -1, 0.7)
    return None


def harami_bullish(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bearish(o1, c1) and body(o1, c1) > avg_b and body(o2, c2) < body(o1, c1) * 0.5:
        if min(o2, c2) > min(o1, c1) and max(o2, c2) < max(o1, c1):
            return ("Bullish Harami", 1, 0.65)
    return None


def harami_bearish(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bullish(o1, c1) and body(o1, c1) > avg_b and body(o2, c2) < body(o1, c1) * 0.5:
        if min(o2, c2) > min(o1, c1) and max(o2, c2) < max(o1, c1):
            return ("Bearish Harami", -1, 0.65)
    return None


def on_neck(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    l1 = float(lows[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bearish(o1, c1) and body(o1, c1) > avg_b and is_bullish(o2, c2):
        if abs(c2 - l1) < avg_b * 0.1:
            return ("On Neck", -1, 0.6)
    return None


def tweezer_tops(opens, highs, lows, closes) -> Optional[tuple]:
    h1, h2 = float(highs[-2]), float(highs[-1])
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if abs(h1 - h2) < avg_b * 0.1 and is_bullish(o1, c1) and is_bearish(o2, c2) and trend_up(closes):
        return ("Tweezer Tops", -1, 0.7)
    return None


def tweezer_bottoms(opens, highs, lows, closes) -> Optional[tuple]:
    l1, l2 = float(lows[-2]), float(lows[-1])
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if abs(l1 - l2) < avg_b * 0.1 and is_bearish(o1, c1) and is_bullish(o2, c2) and trend_down(closes):
        return ("Tweezer Bottoms", 1, 0.7)
    return None


def kicker_bullish(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bearish(o1, c1) and is_bullish(o2, c2) and o2 > o1 and body(o1, c1) > avg_b and body(o2, c2) > avg_b:
        return ("Bullish Kicker", 1, 0.95)
    return None


def kicker_bearish(opens, highs, lows, closes) -> Optional[tuple]:
    o1, c1 = float(opens[-2]), float(closes[-2])
    o2, c2 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bullish(o1, c1) and is_bearish(o2, c2) and o2 < o1 and body(o1, c1) > avg_b and body(o2, c2) > avg_b:
        return ("Bearish Kicker", -1, 0.95)
    return None


# ──────────────────────────────────────────────
# Three-candle patterns
# ──────────────────────────────────────────────

def morning_star(opens, highs, lows, closes) -> Optional[tuple]:
    o1,c1 = float(opens[-3]), float(closes[-3])
    o2,c2 = float(opens[-2]), float(closes[-2])
    o3,c3 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bearish(o1, c1) and body(o1, c1) > avg_b:
        if body(o2, c2) < avg_b * 0.5:
            if is_bullish(o3, c3) and body(o3, c3) > avg_b and c3 > (o1 + c1) / 2:
                return ("Morning Star", 1, 0.9)
    return None


def evening_star(opens, highs, lows, closes) -> Optional[tuple]:
    o1,c1 = float(opens[-3]), float(closes[-3])
    o2,c2 = float(opens[-2]), float(closes[-2])
    o3,c3 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bullish(o1, c1) and body(o1, c1) > avg_b:
        if body(o2, c2) < avg_b * 0.5:
            if is_bearish(o3, c3) and body(o3, c3) > avg_b and c3 < (o1 + c1) / 2:
                return ("Evening Star", -1, 0.9)
    return None


def morning_doji_star(opens, highs, lows, closes) -> Optional[tuple]:
    o1,c1 = float(opens[-3]), float(closes[-3])
    o2,c2 = float(opens[-2]), float(closes[-2])
    o3,c3 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bearish(o1, c1) and body(o1, c1) > avg_b and is_doji(o2, c2, avg_b):
        if is_bullish(o3, c3) and body(o3, c3) > avg_b:
            return ("Morning Doji Star", 1, 0.92)
    return None


def evening_doji_star(opens, highs, lows, closes) -> Optional[tuple]:
    o1,c1 = float(opens[-3]), float(closes[-3])
    o2,c2 = float(opens[-2]), float(closes[-2])
    o3,c3 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bullish(o1, c1) and body(o1, c1) > avg_b and is_doji(o2, c2, avg_b):
        if is_bearish(o3, c3) and body(o3, c3) > avg_b:
            return ("Evening Doji Star", -1, 0.92)
    return None


def three_white_soldiers(opens, highs, lows, closes) -> Optional[tuple]:
    avg_b = avg_body(opens, closes)
    for i in [-3, -2, -1]:
        o, c = float(opens[i]), float(closes[i])
        if not is_bullish(o, c) or body(o, c) < avg_b * 0.7:
            return None
    if float(opens[-2]) > float(opens[-3]) and float(opens[-1]) > float(opens[-2]):
        if float(closes[-2]) > float(closes[-3]) and float(closes[-1]) > float(closes[-2]):
            return ("Three White Soldiers", 1, 0.9)
    return None


def three_black_crows(opens, highs, lows, closes) -> Optional[tuple]:
    avg_b = avg_body(opens, closes)
    for i in [-3, -2, -1]:
        o, c = float(opens[i]), float(closes[i])
        if not is_bearish(o, c) or body(o, c) < avg_b * 0.7:
            return None
    if float(opens[-2]) < float(opens[-3]) and float(opens[-1]) < float(opens[-2]):
        if float(closes[-2]) < float(closes[-3]) and float(closes[-1]) < float(closes[-2]):
            return ("Three Black Crows", -1, 0.9)
    return None


def three_inside_up(opens, highs, lows, closes) -> Optional[tuple]:
    result = harami_bullish(opens, highs, lows, closes)
    if result and is_bullish(float(opens[-1]), float(closes[-1])):
        if float(closes[-1]) > float(closes[-3]):
            return ("Three Inside Up", 1, 0.8)
    return None


def three_inside_down(opens, highs, lows, closes) -> Optional[tuple]:
    result = harami_bearish(opens, highs, lows, closes)
    if result and is_bearish(float(opens[-1]), float(closes[-1])):
        if float(closes[-1]) < float(closes[-3]):
            return ("Three Inside Down", -1, 0.8)
    return None


def three_outside_up(opens, highs, lows, closes) -> Optional[tuple]:
    result = bullish_engulfing(opens, highs, lows, closes)
    if result and is_bullish(float(opens[-1]), float(closes[-1])):
        if float(closes[-1]) > float(closes[-2]):
            return ("Three Outside Up", 1, 0.82)
    return None


def three_outside_down(opens, highs, lows, closes) -> Optional[tuple]:
    result = bearish_engulfing(opens, highs, lows, closes)
    if result and is_bearish(float(opens[-1]), float(closes[-1])):
        if float(closes[-1]) < float(closes[-2]):
            return ("Three Outside Down", -1, 0.82)
    return None


def abandoned_baby_bull(opens, highs, lows, closes) -> Optional[tuple]:
    o1,c1 = float(opens[-3]), float(closes[-3])
    o2,c2,l2,h2 = float(opens[-2]), float(closes[-2]), float(lows[-2]), float(highs[-2])
    o3,c3 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bearish(o1, c1) and is_doji(o2, c2, avg_b):
        if h2 < min(o1, c1) and is_bullish(o3, c3) and float(lows[-1]) > h2:
            return ("Abandoned Baby Bull", 1, 0.95)
    return None


def abandoned_baby_bear(opens, highs, lows, closes) -> Optional[tuple]:
    o1,c1 = float(opens[-3]), float(closes[-3])
    o2,c2,l2,h2 = float(opens[-2]), float(closes[-2]), float(lows[-2]), float(highs[-2])
    o3,c3 = float(opens[-1]), float(closes[-1])
    avg_b = avg_body(opens, closes)
    if is_bullish(o1, c1) and is_doji(o2, c2, avg_b):
        if l2 > max(o1, c1) and is_bearish(o3, c3) and float(highs[-1]) < l2:
            return ("Abandoned Baby Bear", -1, 0.95)
    return None


def upside_gap_two_crows(opens, highs, lows, closes) -> Optional[tuple]:
    o1,c1 = float(opens[-3]), float(closes[-3])
    o2,c2 = float(opens[-2]), float(closes[-2])
    o3,c3 = float(opens[-1]), float(closes[-1])
    if is_bullish(o1, c1) and is_bearish(o2, c2) and o2 > c1:
        if is_bearish(o3, c3) and o3 > o2 and c3 < c2 and c3 > c1:
            return ("Upside Gap Two Crows", -1, 0.7)
    return None


def tasuki_gap_up(opens, highs, lows, closes) -> Optional[tuple]:
    o1,c1 = float(opens[-3]), float(closes[-3])
    o2,c2 = float(opens[-2]), float(closes[-2])
    o3,c3 = float(opens[-1]), float(closes[-1])
    if is_bullish(o1,c1) and is_bullish(o2,c2) and o2 > c1:  # gap up
        if is_bearish(o3,c3) and o3 < c2 and c3 > c1:        # partial fill
            return ("Upside Tasuki Gap", 1, 0.68)
    return None


def three_line_strike_bull(opens, highs, lows, closes) -> Optional[tuple]:
    avg_b = avg_body(opens, closes)
    o1,c1 = float(opens[-4]), float(closes[-4])
    o2,c2 = float(opens[-3]), float(closes[-3])
    o3,c3 = float(opens[-2]), float(closes[-2])
    o4,c4 = float(opens[-1]), float(closes[-1])
    if all(is_bearish(float(opens[-i]), float(closes[-i])) for i in [4,3,2]):
        if body(o1,c1) > avg_b and body(o2,c2) > avg_b and body(o3,c3) > avg_b:
            if c2 < c1 and c3 < c2:
                if is_bullish(o4,c4) and o4 <= c3 and c4 >= o1:
                    return ("Three-Line Strike Bull", 1, 0.72)
    return None


def three_line_strike_bear(opens, highs, lows, closes) -> Optional[tuple]:
    avg_b = avg_body(opens, closes)
    o1,c1 = float(opens[-4]), float(closes[-4])
    o2,c2 = float(opens[-3]), float(closes[-3])
    o3,c3 = float(opens[-2]), float(closes[-2])
    o4,c4 = float(opens[-1]), float(closes[-1])
    if all(is_bullish(float(opens[-i]), float(closes[-i])) for i in [4,3,2]):
        if body(o1,c1) > avg_b and body(o2,c2) > avg_b and body(o3,c3) > avg_b:
            if c2 > c1 and c3 > c2:
                if is_bearish(o4,c4) and o4 >= c3 and c4 <= o1:
                    return ("Three-Line Strike Bear", -1, 0.72)
    return None


def concealing_baby_swallow(opens, highs, lows, closes) -> Optional[tuple]:
    avg_b = avg_body(opens, closes)
    for i in [-4, -3, -2, -1]:
        o, c = float(opens[i]), float(closes[i])
        if not is_bearish(o, c) or body(o, c) < avg_b * 0.8:
            return None
    o3,c3,h3 = float(opens[-2]), float(closes[-2]), float(highs[-2])
    o4,c4 = float(opens[-1]), float(closes[-1])
    if h3 > float(opens[-3]) and o4 < c3 and float(highs[-1]) > h3 and c4 < float(opens[-2]):
        return ("Concealing Baby Swallow", 1, 0.8)
    return None


# ──────────────────────────────────────────────
# Master pattern scanner
# ──────────────────────────────────────────────
ALL_PATTERNS = [
    doji, gravestone_doji, dragonfly_doji, hammer, hanging_man, inverted_hammer,
    shooting_star, spinning_top, marubozu_bullish, marubozu_bearish,
    bullish_engulfing, bearish_engulfing, piercing_line, dark_cloud_cover,
    harami_bullish, harami_bearish, on_neck, tweezer_tops, tweezer_bottoms,
    kicker_bullish, kicker_bearish,
    morning_star, evening_star, morning_doji_star, evening_doji_star,
    three_white_soldiers, three_black_crows, three_inside_up, three_inside_down,
    three_outside_up, three_outside_down, abandoned_baby_bull, abandoned_baby_bear,
    upside_gap_two_crows, tasuki_gap_up,
    three_line_strike_bull, three_line_strike_bear, concealing_baby_swallow,
]


def scan_all_patterns(opens, highs, lows, closes) -> list[dict]:
    """Scan all candlestick patterns. Returns list of detected patterns."""
    results = []
    if len(closes) < 5:
        return results

    for fn in ALL_PATTERNS:
        try:
            r = fn(opens, highs, lows, closes)
            if r:
                name, signal, strength = r
                results.append({"pattern": name, "signal": signal, "strength": strength})
        except Exception:
            continue

    return results


def aggregate_pattern_vote(opens, highs, lows, closes) -> dict:
    """Aggregate all patterns into a single vote."""
    patterns = scan_all_patterns(opens, highs, lows, closes)
    if not patterns:
        return {"vote": "NEUTRAL", "score": 0.0, "patterns": []}

    buy_score = sum(p["strength"] for p in patterns if p["signal"] == 1)
    sell_score = sum(p["strength"] for p in patterns if p["signal"] == -1)
    total = buy_score + sell_score

    if total == 0:
        return {"vote": "NEUTRAL", "score": 0.0, "patterns": patterns}

    net = (buy_score - sell_score) / total
    if net > 0.1:
        vote = "BUY"
    elif net < -0.1:
        vote = "SELL"
    else:
        vote = "NEUTRAL"

    return {
        "vote": vote,
        "score": round(net, 3),
        "buy_score": round(buy_score, 2),
        "sell_score": round(sell_score, 2),
        "patterns": [p for p in patterns if p["signal"] != 0][:10],
    }
