"""Extended Technical Analysis Schools — Groups 4.1 through 4.12
Schools 30–74 (45 additional schools) for The Market Lion.
Each function returns SchoolResult(name, vote, strength, confidence, details).
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional

from indicators import SchoolResult, Vote, sma, ema, wma, atr, rsi, safe_div


# ─── GROUP 4.1: DOW THEORY ───────────────────────────────────────────────────

def analyze_dow_theory(df: pd.DataFrame) -> SchoolResult:
    """School 30 — Dow Theory: trend, phases, confirmation, volume."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))

    n = len(close)
    if n < 60:
        return SchoolResult("Dow Theory", Vote.NEUTRAL, 0.3, 0.4, {"error": "insufficient data"})

    # Primary trend: 20 vs 60 bar swing
    recent_high = np.max(high[-20:])
    recent_low = np.min(low[-20:])
    prior_high = np.max(high[-60:-20])
    prior_low = np.min(low[-60:-20])

    higher_highs = recent_high > prior_high
    higher_lows = recent_low > prior_low
    lower_highs = recent_high < prior_high
    lower_lows = recent_low < prior_low

    uptrend = higher_highs and higher_lows
    downtrend = lower_highs and lower_lows

    # Volume confirmation: volume should expand in trend direction
    price_change = close[-1] - close[-20]
    vol_change = np.mean(volume[-5:]) - np.mean(volume[-20:-5])
    vol_confirms = (price_change > 0 and vol_change > 0) or (price_change < 0 and vol_change > 0)

    # Market phases approximation using MA relationships
    ma20 = sma(close, 20)[-1]
    ma60 = sma(close, 60)[-1] if n >= 60 else close[-1]
    price = close[-1]

    # Accumulation: price near lows, flat MAs; Distribution: price near highs, flat MAs
    price_pct_range = safe_div(price - np.min(low[-60:]), np.max(high[-60:]) - np.min(low[-60:]))

    score = 0.0
    if uptrend:
        score += 0.5
    elif downtrend:
        score -= 0.5
    if price > ma20 > ma60:
        score += 0.3
    elif price < ma20 < ma60:
        score -= 0.3
    if vol_confirms:
        score += 0.15 * np.sign(score) if score != 0 else 0

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    details = {
        "uptrend": uptrend, "downtrend": downtrend,
        "higher_highs": higher_highs, "higher_lows": higher_lows,
        "lower_highs": lower_highs, "lower_lows": lower_lows,
        "volume_confirms": vol_confirms,
        "price_pct_range_60": round(price_pct_range, 3),
        "ma20": round(ma20, 5), "ma60": round(ma60, 5),
    }
    return SchoolResult("Dow Theory", vote, abs(score), 0.80, details)


# ─── GROUP 4.2: ICT / SMC EXTENDED ──────────────────────────────────────────

def analyze_ict_full(df: pd.DataFrame) -> SchoolResult:
    """School 31 — ICT Full: Killzones, Power of 3, OTE, Judas Swing."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 30:
        return SchoolResult("ICT Full", Vote.NEUTRAL, 0.3, 0.4, {})

    # OTE (Optimal Trade Entry): 61.8%–79% retracement of a swing
    swing_high = np.max(high[-20:])
    swing_low = np.min(low[-20:])
    swing_range = swing_high - swing_low
    price = close[-1]

    ote_bull_low = swing_low + 0.618 * swing_range
    ote_bull_high = swing_low + 0.79 * swing_range
    ote_bear_low = swing_high - 0.79 * swing_range
    ote_bear_high = swing_high - 0.618 * swing_range

    in_bull_ote = ote_bull_low <= price <= ote_bull_high
    in_bear_ote = ote_bear_low <= price <= ote_bear_high

    # Power of 3: accumulation → manipulation → distribution
    # Approximated: look for a false move then reversal
    mid5 = np.mean(close[-5:])
    mid10_15 = np.mean(close[-15:-10])
    manipulation_spike = abs(np.max(high[-5:]) - np.min(low[-5:])) > 1.5 * abs(np.max(high[-15:-10]) - np.min(low[-15:-10]))

    # Judas Swing: early session high/low swept before reversal
    # Approximate: price broke prior high/low then reversed
    prev_high = np.max(high[-10:-5])
    prev_low = np.min(low[-10:-5])
    judas_bull = np.min(low[-5:]) < prev_low and close[-1] > prev_low
    judas_bear = np.max(high[-5:]) > prev_high and close[-1] < prev_high

    score = 0.0
    if in_bull_ote:
        score += 0.5
    if in_bear_ote:
        score -= 0.5
    if judas_bull:
        score += 0.3
    if judas_bear:
        score -= 0.3
    if manipulation_spike and score > 0:
        score += 0.15
    elif manipulation_spike and score < 0:
        score -= 0.15

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("ICT Full", vote, abs(score), 0.76, {
        "in_bull_ote": in_bull_ote, "in_bear_ote": in_bear_ote,
        "judas_bull": judas_bull, "judas_bear": judas_bear,
        "manipulation_spike": manipulation_spike,
        "ote_bull_zone": (round(ote_bull_low, 5), round(ote_bull_high, 5)),
    })


def analyze_ipda(df: pd.DataFrame) -> SchoolResult:
    """School 32 — IPDA (Interbank Price Delivery Algorithm): quarterly shifts, draw on liquidity."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 60:
        return SchoolResult("IPDA", Vote.NEUTRAL, 0.3, 0.5, {})

    # IPDA looks 20, 40, 60 bars back for premium/discount arrays
    lookbacks = [20, 40, 60]
    price = close[-1]
    score = 0.0
    details = {}

    for lb in lookbacks:
        if n < lb:
            continue
        h = np.max(high[-lb:])
        l = np.min(low[-lb:])
        mid = (h + l) / 2
        # Discount: price below midpoint (buy zone), Premium: above (sell zone)
        pct = safe_div(price - l, h - l)
        details[f"pct_in_range_{lb}"] = round(pct, 3)
        details[f"high_{lb}"] = round(h, 5)
        details[f"low_{lb}"] = round(l, 5)
        if pct < 0.35:   # discount
            score += 0.25
        elif pct > 0.65:  # premium
            score -= 0.25

    # Draw on liquidity: price approaching significant high/low
    dist_to_high = abs(price - np.max(high[-60:])) / price
    dist_to_low = abs(price - np.min(low[-60:])) / price
    draw_to_high = dist_to_high < 0.005
    draw_to_low = dist_to_low < 0.005
    details["draw_to_high"] = draw_to_high
    details["draw_to_low"] = draw_to_low

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("IPDA", vote, abs(score), 0.72, details)


def analyze_liquidity_theory(df: pd.DataFrame) -> SchoolResult:
    """School 33 — Liquidity Theory & Stop Hunts: BSL/SSL levels, equal highs/lows."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Liquidity Theory", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    # Buy-side liquidity (BSL): clusters of equal highs = stops above
    # Sell-side liquidity (SSL): clusters of equal lows = stops below
    tolerance = np.std(close[-20:]) * 0.1

    highs_20 = high[-20:]
    lows_20 = low[-20:]

    # Equal highs: count how many highs are within tolerance of max
    max_high = np.max(highs_20)
    min_low = np.min(lows_20)
    equal_highs = np.sum(np.abs(highs_20 - max_high) < tolerance)
    equal_lows = np.sum(np.abs(lows_20 - min_low) < tolerance)

    # Stop hunt: recent wick beyond equal high/low followed by reversal
    recent_high_wick = np.max(high[-3:])
    recent_low_wick = np.min(low[-3:])
    swept_high = recent_high_wick > max_high and price < max_high  # hunted highs, now below
    swept_low = recent_low_wick < min_low and price > min_low       # hunted lows, now above

    score = 0.0
    if swept_low:
        score += 0.6   # liquidity swept below, expect bullish reversal
    if swept_high:
        score -= 0.6   # liquidity swept above, expect bearish reversal
    if equal_lows >= 2 and not swept_low:
        score += 0.2   # SSL pool building below, draw toward it (eventual buy after sweep)
    if equal_highs >= 2 and not swept_high:
        score -= 0.2

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Liquidity Theory", vote, abs(score), 0.74, {
        "equal_highs_count": int(equal_highs), "equal_lows_count": int(equal_lows),
        "swept_high": swept_high, "swept_low": swept_low,
        "bsl_level": round(max_high, 5), "ssl_level": round(min_low, 5),
    })


def analyze_naked_trading(df: pd.DataFrame) -> SchoolResult:
    """School 34 — Naked Trading: price action without indicators, key S/R, patterns."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    open_ = df['open'].values if 'open' in df.columns else close.copy()
    n = len(close)
    if n < 20:
        return SchoolResult("Naked Trading", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    # Key S/R from recent swing highs/lows
    lookback = min(n, 50)
    h = high[-lookback:]
    l = low[-lookback:]

    # Find local swing highs and lows
    swing_highs = []
    swing_lows = []
    for i in range(2, len(h) - 2):
        if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]:
            swing_highs.append(h[i])
        if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]:
            swing_lows.append(l[i])

    nearest_resistance = min(swing_highs, key=lambda x: abs(x - price) if x > price else float('inf')) if swing_highs else price * 1.01
    nearest_support = max(swing_lows, key=lambda x: x if x < price else float('-inf')) if swing_lows else price * 0.99

    dist_to_res = safe_div(nearest_resistance - price, price)
    dist_to_sup = safe_div(price - nearest_support, price)

    # Pin bar / rejection candle
    body = abs(close[-1] - open_[-1])
    candle_range = high[-1] - low[-1]
    upper_wick = high[-1] - max(close[-1], open_[-1])
    lower_wick = min(close[-1], open_[-1]) - low[-1]
    pin_bull = lower_wick > 2 * body and lower_wick > upper_wick
    pin_bear = upper_wick > 2 * body and upper_wick > lower_wick

    score = 0.0
    # Closer to support = more bullish
    if dist_to_sup < dist_to_res:
        score += 0.3
    else:
        score -= 0.3
    if pin_bull:
        score += 0.4
    if pin_bear:
        score -= 0.4

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Naked Trading", vote, abs(score), 0.72, {
        "nearest_resistance": round(nearest_resistance, 5),
        "nearest_support": round(nearest_support, 5),
        "dist_to_resistance_pct": round(dist_to_res * 100, 3),
        "dist_to_support_pct": round(dist_to_sup * 100, 3),
        "pin_bar_bull": pin_bull, "pin_bar_bear": pin_bear,
    })


def analyze_order_flow(df: pd.DataFrame) -> SchoolResult:
    """School 35 — Order Flow: cumulative delta, volume imbalance, absorption."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 10:
        return SchoolResult("Order Flow", Vote.NEUTRAL, 0.3, 0.5, {})

    # Approximate cumulative delta: bullish bar = +vol, bearish bar = -vol
    deltas = np.where(close > close[0:1], volume, -volume)
    for i in range(1, n):
        deltas[i] = volume[i] if close[i] >= close[i-1] else -volume[i]

    cum_delta = np.cumsum(deltas)
    delta_20 = cum_delta[-1] - cum_delta[max(0, n-20)]

    # Volume absorption: large volume + small price move = absorption
    price_move_20 = abs(close[-1] - close[-20]) if n >= 20 else 0
    avg_vol = np.mean(volume[-20:])
    total_vol_20 = np.sum(volume[-20:])
    absorption = total_vol_20 > 2 * avg_vol * 20 and price_move_20 < np.std(close[-20:]) * 0.5

    # Buying/selling pressure from close position in bar
    buy_pressure = np.mean(safe_div(close[-10:] - low[-10:], high[-10:] - low[-10:] + 1e-10))
    sell_pressure = 1 - buy_pressure

    score = 0.0
    if delta_20 > 0:
        score += min(0.5, delta_20 / (total_vol_20 + 1e-10))
    else:
        score += max(-0.5, delta_20 / (total_vol_20 + 1e-10))

    score += (buy_pressure - 0.5) * 0.5

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Order Flow", vote, abs(score), 0.70, {
        "cumulative_delta_20": round(float(delta_20), 2),
        "buy_pressure": round(float(buy_pressure), 3),
        "sell_pressure": round(float(sell_pressure), 3),
        "absorption_detected": bool(absorption),
    })


def analyze_supply_demand_zones(df: pd.DataFrame) -> SchoolResult:
    """School 36 — Supply & Demand Zones: base + impulse identification."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 30:
        return SchoolResult("Supply & Demand Zones", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    atr_val = float(np.nanmean(atr(high, low, close, 14)[-20:]))

    # Identify impulse moves: candles with range > 1.5x ATR
    ranges = high - low
    impulse_threshold = 1.5 * atr_val
    demand_zones = []
    supply_zones = []

    for i in range(5, n - 2):
        # Impulse up from a base
        if ranges[i] > impulse_threshold and close[i] > close[i-1]:
            base_low = np.min(low[max(0, i-3):i])
            base_high = np.max(high[max(0, i-3):i])
            demand_zones.append((base_low, base_high))
        # Impulse down from a base
        if ranges[i] > impulse_threshold and close[i] < close[i-1]:
            base_low = np.min(low[max(0, i-3):i])
            base_high = np.max(high[max(0, i-3):i])
            supply_zones.append((base_low, base_high))

    # Find nearest untested zones
    in_demand = any(zl <= price <= zh for zl, zh in demand_zones[-5:])
    in_supply = any(zl <= price <= zh for zl, zh in supply_zones[-5:])

    score = 0.0
    if in_demand:
        score += 0.6
    if in_supply:
        score -= 0.6
    # Trend of recent closes
    if close[-1] > close[-5]:
        score += 0.2
    else:
        score -= 0.2

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Supply & Demand Zones", vote, abs(score), 0.75, {
        "in_demand_zone": in_demand, "in_supply_zone": in_supply,
        "demand_zones_found": len(demand_zones), "supply_zones_found": len(supply_zones),
        "atr": round(atr_val, 5),
    })


# ─── GROUP 4.3: CLASSIC CHARTING METHODS ─────────────────────────────────────

def analyze_andrews_pitchfork(df: pd.DataFrame) -> SchoolResult:
    """School 37 — Andrews Pitchfork: median line channels."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 30:
        return SchoolResult("Andrews Pitchfork", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]

    # Find pivot points: A (first extreme), B, C for pitchfork construction
    # Using simplified 3-pivot approach on recent data
    p1_idx = np.argmax(high[-30:-15]) + (n - 30)
    p2_idx = np.argmin(low[-15:]) + (n - 15)
    p3_idx = np.argmax(high[-10:]) + (n - 10)

    p1 = (p1_idx, high[p1_idx])
    p2 = (p2_idx, low[p2_idx])
    p3 = (p3_idx, high[p3_idx])

    # Median line midpoint from B and C
    mid_price = (p2[1] + p3[1]) / 2
    # Pitchfork slope approximation
    slope = safe_div(mid_price - p1[1], (p2[0] + p3[0]) / 2 - p1[0])

    bars_from_p1 = n - 1 - p1[0]
    median_line = p1[1] + slope * bars_from_p1
    upper_line = median_line + (p3[1] - mid_price)
    lower_line = median_line - (mid_price - p2[1])

    in_upper_half = price > median_line
    near_median = abs(price - median_line) < abs(upper_line - lower_line) * 0.1
    touching_lower = price < lower_line * 1.005

    score = 0.0
    if touching_lower:
        score += 0.5
    elif in_upper_half:
        score += 0.2
    else:
        score -= 0.2
    if near_median:
        score *= 0.5  # neutral at median

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("Andrews Pitchfork", vote, abs(score), 0.68, {
        "median_line": round(median_line, 5),
        "upper_line": round(upper_line, 5),
        "lower_line": round(lower_line, 5),
        "price_above_median": bool(in_upper_half),
        "near_median": bool(near_median),
    })


def analyze_point_figure(df: pd.DataFrame) -> SchoolResult:
    """School 38 — Point & Figure: box reversal signals, bullish/bearish counts."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Point & Figure", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    atr_val = float(np.nanmean(atr(high, low, close, 14)[-20:]))
    box_size = atr_val * 0.5  # dynamic box size
    reversal = 3  # standard 3-box reversal

    # Build P&F chart
    pf_column = []   # list of (direction, price_level)
    direction = 1    # 1=X (up), -1=O (down)
    current_level = close[0]

    xs = [current_level]
    os = []
    current_col_type = 'X' if close[1] > close[0] else 'O'
    col_start = close[0]

    for i in range(1, n):
        if current_col_type == 'X':
            if close[i] >= col_start + box_size:
                col_start += box_size * int((close[i] - col_start) / box_size)
                xs.append(col_start)
            elif close[i] <= col_start - reversal * box_size:
                current_col_type = 'O'
                col_start = col_start - box_size
                os.append(col_start)
        else:
            if close[i] <= col_start - box_size:
                col_start -= box_size * int((col_start - close[i]) / box_size)
                os.append(col_start)
            elif close[i] >= col_start + reversal * box_size:
                current_col_type = 'X'
                col_start = col_start + box_size
                xs.append(col_start)

    # Signal: currently in X column (bullish) or O column (bearish)
    bullish = current_col_type == 'X'
    # Bull trap / double top
    double_top_buy = bullish and len(xs) >= 2 and price > max(xs[:-1]) if xs else False

    score = 0.5 if bullish else -0.5
    if double_top_buy:
        score = 0.75

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Point & Figure", vote, abs(score), 0.70, {
        "current_column": current_col_type,
        "box_size": round(box_size, 5),
        "bullish": bullish,
        "double_top_buy": bool(double_top_buy),
    })


def analyze_darvas_box(df: pd.DataFrame) -> SchoolResult:
    """School 39 — Darvas Box: box formation and breakout signals."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Darvas Box", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    # Build Darvas boxes: new high + consolidation = box top; consolidation low = box bottom
    box_top = None
    box_bottom = None
    in_box = False

    for i in range(3, n):
        if box_top is None:
            if high[i] > np.max(high[max(0, i-3):i]):
                box_top = high[i]
                in_box = True
        elif in_box:
            if high[i] > box_top:
                box_top = high[i]
            if box_bottom is None:
                if low[i] < np.min(low[max(0, i-3):i]):
                    box_bottom = low[i]
            else:
                if low[i] < box_bottom:
                    box_bottom = low[i]

    if box_top is None:
        box_top = np.max(high[-10:])
    if box_bottom is None:
        box_bottom = np.min(low[-10:])

    breakout_up = price > box_top * 1.001
    breakout_down = price < box_bottom * 0.999
    in_box_now = box_bottom <= price <= box_top

    score = 0.0
    if breakout_up:
        score = 0.75
    elif breakout_down:
        score = -0.75
    elif in_box_now:
        pct = safe_div(price - box_bottom, box_top - box_bottom)
        score = (pct - 0.5) * 0.4

    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Darvas Box", vote, abs(score), 0.72, {
        "box_top": round(box_top, 5), "box_bottom": round(box_bottom, 5),
        "breakout_up": breakout_up, "breakout_down": breakout_down, "in_box": in_box_now,
    })


def analyze_weinstein_stages(df: pd.DataFrame) -> SchoolResult:
    """School 40 — Weinstein Stage Analysis: 4 stages using 30-week MA."""
    close = df['close'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 30:
        return SchoolResult("Weinstein Stages", Vote.NEUTRAL, 0.3, 0.5, {})

    # Use 30-bar MA as Weinstein's 30-week MA equivalent
    ma30 = sma(close, min(30, n))
    price = close[-1]
    ma_cur = ma30[-1]
    ma_prev = ma30[-5] if n > 5 else ma30[0]

    ma_rising = ma_cur > ma_prev
    ma_falling = ma_cur < ma_prev
    price_above = price > ma_cur
    price_below = price < ma_cur

    # Volume trend
    vol_avg_recent = np.mean(volume[-10:])
    vol_avg_prior = np.mean(volume[-30:-10]) if n >= 30 else np.mean(volume)
    vol_expanding = vol_avg_recent > vol_avg_prior

    # Stage identification:
    # Stage 1: Basing — flat MA, price neutral, low vol
    # Stage 2: Advancing — rising MA, price above, expanding vol (BUY)
    # Stage 3: Topping — flat MA after advance, price at highs
    # Stage 4: Declining — falling MA, price below (SELL)

    if price_above and ma_rising and vol_expanding:
        stage = 2; score = 0.75
    elif price_below and ma_falling:
        stage = 4; score = -0.75
    elif not ma_rising and not ma_falling and price_above:
        stage = 3; score = -0.2
    else:
        stage = 1; score = 0.1

    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Weinstein Stages", vote, abs(score), 0.76, {
        "stage": stage,
        "ma30": round(ma_cur, 5),
        "ma_rising": bool(ma_rising),
        "price_above_ma": bool(price_above),
        "volume_expanding": bool(vol_expanding),
    })


def analyze_bill_williams(df: pd.DataFrame) -> SchoolResult:
    """School 41 — Bill Williams: Alligator, AO, AC, Fractals, MFI."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 34:
        return SchoolResult("Bill Williams", Vote.NEUTRAL, 0.3, 0.5, {})

    hl2 = (high + low) / 2

    # Alligator: jaw=13/8, teeth=8/5, lips=5/3 (SMMA approximation using EMA)
    jaw = sma(hl2, 13)
    teeth = sma(hl2, 8)
    lips = sma(hl2, 5)
    price = close[-1]

    alligator_open = lips[-1] > teeth[-1] > jaw[-1]   # bullish
    alligator_open_bear = lips[-1] < teeth[-1] < jaw[-1]  # bearish
    alligator_sleeping = abs(lips[-1] - teeth[-1]) < abs(lips[-5] - teeth[-5]) * 0.7

    # Awesome Oscillator: SMA(5, hl2) - SMA(34, hl2)
    ao = sma(hl2, 5) - sma(hl2, 34)
    ao_cur = ao[-1]; ao_prev = ao[-2]
    ao_bull = ao_cur > 0 and ao_cur > ao_prev
    ao_bear = ao_cur < 0 and ao_cur < ao_prev
    ao_saucer_bull = ao_cur > 0 and ao_prev < ao[-2 - 1] if n > 3 else False

    # Fractals: 5-bar fractal (high fractal = sell, low fractal = buy)
    fractal_buy = n >= 5 and low[-3] < low[-5] and low[-3] < low[-4] and low[-3] < low[-2] and low[-3] < low[-1]
    fractal_sell = n >= 5 and high[-3] > high[-5] and high[-3] > high[-4] and high[-3] > high[-2] and high[-3] > high[-1]

    score = 0.0
    if alligator_open:
        score += 0.35
    if alligator_open_bear:
        score -= 0.35
    if ao_bull:
        score += 0.25
    if ao_bear:
        score -= 0.25
    if fractal_buy:
        score += 0.2
    if fractal_sell:
        score -= 0.2

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Bill Williams", vote, abs(score), 0.75, {
        "alligator_open_bullish": alligator_open,
        "alligator_open_bearish": alligator_open_bear,
        "alligator_sleeping": alligator_sleeping,
        "ao": round(float(ao_cur), 5),
        "ao_bullish": ao_bull, "ao_bearish": ao_bear,
        "fractal_buy": fractal_buy, "fractal_sell": fractal_sell,
        "jaw": round(float(jaw[-1]), 5), "teeth": round(float(teeth[-1]), 5), "lips": round(float(lips[-1]), 5),
    })


def analyze_turtle_trading(df: pd.DataFrame) -> SchoolResult:
    """School 42 — Turtle Trading: 20/55-day breakout system."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 55:
        return SchoolResult("Turtle Trading", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]

    # System 1: 20-bar breakout (entry), 10-bar breakout (exit)
    high20 = np.max(high[-21:-1])
    low20 = np.min(low[-21:-1])
    high10 = np.max(high[-11:-1])
    low10 = np.min(low[-11:-1])

    # System 2: 55-bar breakout
    high55 = np.max(high[-56:-1])
    low55 = np.min(low[-56:-1])

    s1_long = price > high20
    s1_short = price < low20
    s2_long = price > high55
    s2_short = price < low55

    # ATR-based position sizing (N)
    atr_val = float(np.nanmean(atr(high, low, close, 20)[-5:]))

    score = 0.0
    if s2_long:
        score += 0.8
    elif s1_long:
        score += 0.5
    if s2_short:
        score -= 0.8
    elif s1_short:
        score -= 0.5

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Turtle Trading", vote, abs(score), 0.78, {
        "s1_long": s1_long, "s1_short": s1_short,
        "s2_long": s2_long, "s2_short": s2_short,
        "20d_high": round(high20, 5), "20d_low": round(low20, 5),
        "55d_high": round(high55, 5), "55d_low": round(low55, 5),
        "atr_N": round(atr_val, 5),
    })


def analyze_trendlines_channels(df: pd.DataFrame) -> SchoolResult:
    """School 43 — Trend Lines & Channels: linear regression channel position."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Trend Lines & Channels", Vote.NEUTRAL, 0.3, 0.5, {})

    lookback = min(n, 50)
    x = np.arange(lookback)
    y = close[-lookback:]

    # Linear regression
    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]
    reg_line = np.polyval(coeffs, x)
    residuals = y - reg_line
    std_resid = np.std(residuals)

    price = close[-1]
    reg_now = np.polyval(coeffs, lookback - 1)
    upper_channel = reg_now + 2 * std_resid
    lower_channel = reg_now - 2 * std_resid

    pct_in_channel = safe_div(price - lower_channel, upper_channel - lower_channel)
    slope_pct = safe_div(slope, np.mean(y)) * 100  # slope as % per bar

    score = 0.0
    if slope > 0:
        score += 0.4
    else:
        score -= 0.4

    if pct_in_channel < 0.1:
        score += 0.4   # near lower channel — bounce potential
    elif pct_in_channel > 0.9:
        score -= 0.4   # near upper channel — reversal potential
    elif pct_in_channel > 0.5:
        score += 0.15
    else:
        score -= 0.15

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Trend Lines & Channels", vote, abs(score), 0.75, {
        "slope": round(float(slope), 6),
        "slope_pct_per_bar": round(float(slope_pct), 4),
        "regression_line": round(float(reg_now), 5),
        "upper_channel": round(float(upper_channel), 5),
        "lower_channel": round(float(lower_channel), 5),
        "position_in_channel": round(float(pct_in_channel), 3),
    })


# ─── GROUP 4.4: CYCLES ───────────────────────────────────────────────────────

def analyze_hurst_cycles(df: pd.DataFrame) -> SchoolResult:
    """School 44 — Hurst Cycles: dominant cycle detection via autocorrelation."""
    close = df['close'].values
    n = len(close)
    if n < 60:
        return SchoolResult("Hurst Cycles", Vote.NEUTRAL, 0.3, 0.4, {})

    # Find dominant cycle via autocorrelation
    detrended = close - sma(close, min(n, 40))
    detrended = detrended[~np.isnan(detrended)]
    if len(detrended) < 20:
        return SchoolResult("Hurst Cycles", Vote.NEUTRAL, 0.3, 0.4, {})

    # Autocorrelation for lags 5..40
    best_lag = 20
    best_corr = 0.0
    for lag in range(5, min(41, len(detrended) // 2)):
        corr = np.corrcoef(detrended[:-lag], detrended[lag:])[0, 1]
        if not np.isnan(corr) and corr > best_corr:
            best_corr = corr
            best_lag = lag

    # Phase within dominant cycle
    phase = (n % best_lag) / best_lag  # 0 = cycle bottom, 0.5 = cycle top
    price = close[-1]
    cycle_mid = np.mean(close[-best_lag:]) if n >= best_lag else np.mean(close)

    score = 0.0
    if phase < 0.25:     # early ascending — buy
        score = 0.6
    elif phase < 0.5:    # late ascending
        score = 0.3
    elif phase < 0.75:   # early descending — sell
        score = -0.3
    else:                # late descending — near bottom
        score = -0.1

    if price > cycle_mid:
        score += 0.1
    else:
        score -= 0.1

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Hurst Cycles", vote, abs(score), 0.65, {
        "dominant_cycle_bars": best_lag,
        "cycle_correlation": round(best_corr, 3),
        "phase": round(phase, 3),
        "cycle_midpoint": round(cycle_mid, 5),
    })


def analyze_kondratieff(df: pd.DataFrame) -> SchoolResult:
    """School 45 — Kondratieff Wave: long-term macro cycle positioning."""
    close = df['close'].values
    n = len(close)
    if n < 100:
        return SchoolResult("Kondratieff Wave", Vote.NEUTRAL, 0.3, 0.4, {})

    # Approximate long wave using very long MAs and their trend
    ma50 = sma(close, min(50, n))
    ma100 = sma(close, min(100, n))
    price = close[-1]

    ma50_cur = ma50[-1]; ma50_old = ma50[-min(20, n//2)]
    ma100_cur = ma100[-1]; ma100_old = ma100[-min(20, n//2)]

    long_uptrend = ma50_cur > ma100_cur and ma50_cur > ma50_old
    long_downtrend = ma50_cur < ma100_cur and ma50_cur < ma50_old

    # Commodity proxy: long-term volatility expansion = inflationary (K-wave spring/summer)
    vol_long = np.std(close[-100:]) if n >= 100 else np.std(close)
    vol_recent = np.std(close[-20:])
    vol_ratio = safe_div(vol_recent, vol_long)

    score = 0.0
    if long_uptrend:
        score += 0.4
    elif long_downtrend:
        score -= 0.4
    if price > ma100_cur:
        score += 0.2
    else:
        score -= 0.2
    if vol_ratio > 1.2:
        score *= 0.8  # high volatility = uncertainty, reduce confidence

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("Kondratieff Wave", vote, abs(score), 0.55, {
        "long_uptrend": bool(long_uptrend),
        "long_downtrend": bool(long_downtrend),
        "ma50": round(float(ma50_cur), 5),
        "ma100": round(float(ma100_cur), 5),
        "volatility_ratio": round(float(vol_ratio), 3),
    })


# ─── GROUP 4.5: VOLUME / MARKET MICROSTRUCTURE ───────────────────────────────

def analyze_market_profile(df: pd.DataFrame) -> SchoolResult:
    """School 46 — Market Profile (TPO): POC, VAH, VAL, balance/imbalance."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 20:
        return SchoolResult("Market Profile", Vote.NEUTRAL, 0.3, 0.5, {})

    lookback = min(n, 50)
    h_arr = high[-lookback:]
    l_arr = low[-lookback:]
    v_arr = volume[-lookback:]

    # Build price histogram with 20 buckets
    price_min = np.min(l_arr)
    price_max = np.max(h_arr)
    if price_max == price_min:
        return SchoolResult("Market Profile", Vote.NEUTRAL, 0.3, 0.5, {})

    buckets = 20
    bucket_size = (price_max - price_min) / buckets
    hist = np.zeros(buckets)

    for i in range(lookback):
        b_low = int((l_arr[i] - price_min) / bucket_size)
        b_high = int((h_arr[i] - price_min) / bucket_size)
        b_low = max(0, min(buckets - 1, b_low))
        b_high = max(0, min(buckets - 1, b_high))
        for b in range(b_low, b_high + 1):
            hist[b] += v_arr[i] / max(1, b_high - b_low + 1)

    poc_bucket = np.argmax(hist)
    poc = price_min + (poc_bucket + 0.5) * bucket_size

    # Value Area: 70% of volume
    total_vol = np.sum(hist)
    target = total_vol * 0.70
    va_vol = hist[poc_bucket]
    va_buckets = [poc_bucket]
    lo, hi = poc_bucket, poc_bucket
    while va_vol < target and (lo > 0 or hi < buckets - 1):
        add_low = hist[lo - 1] if lo > 0 else -1
        add_high = hist[hi + 1] if hi < buckets - 1 else -1
        if add_high >= add_low and hi < buckets - 1:
            hi += 1; va_buckets.append(hi); va_vol += hist[hi]
        elif lo > 0:
            lo -= 1; va_buckets.append(lo); va_vol += hist[lo]
        else:
            break

    vah = price_min + (max(va_buckets) + 1) * bucket_size
    val = price_min + min(va_buckets) * bucket_size
    price = close[-1]

    score = 0.0
    if price > vah:
        score = 0.5    # above value area — bullish
    elif price < val:
        score = -0.5   # below value area — bearish
    elif price > poc:
        score = 0.2
    else:
        score = -0.2

    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Market Profile", vote, abs(score), 0.75, {
        "poc": round(poc, 5), "vah": round(vah, 5), "val": round(val, 5),
        "price_vs_poc": "above" if price > poc else "below",
        "price_in_value_area": bool(val <= price <= vah),
    })


def analyze_volume_profile(df: pd.DataFrame) -> SchoolResult:
    """School 47 — Volume Profile: HVN, LVN, POC for current session."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 10:
        return SchoolResult("Volume Profile", Vote.NEUTRAL, 0.3, 0.5, {})

    lookback = min(n, 30)
    price = close[-1]
    price_min = np.min(low[-lookback:])
    price_max = np.max(high[-lookback:])
    if price_max == price_min:
        return SchoolResult("Volume Profile", Vote.NEUTRAL, 0.3, 0.5, {})

    buckets = 15
    bucket_size = (price_max - price_min) / buckets
    hist = np.zeros(buckets)
    for i in range(lookback):
        b = int((close[-lookback + i] - price_min) / bucket_size)
        b = max(0, min(buckets - 1, b))
        hist[b] += volume[-lookback + i]

    avg_vol_bucket = np.mean(hist)
    hvn_threshold = avg_vol_bucket * 1.3
    lvn_threshold = avg_vol_bucket * 0.7

    price_bucket = int((price - price_min) / bucket_size)
    price_bucket = max(0, min(buckets - 1, price_bucket))

    at_hvn = hist[price_bucket] >= hvn_threshold
    at_lvn = hist[price_bucket] <= lvn_threshold

    poc_bucket = np.argmax(hist)
    poc = price_min + (poc_bucket + 0.5) * bucket_size

    score = 0.0
    if price > poc:
        score += 0.3
    else:
        score -= 0.3
    if at_lvn and price > poc:
        score += 0.3   # LVN above POC = price likely to accelerate upward
    if at_lvn and price < poc:
        score -= 0.3
    if at_hvn:
        score *= 0.5   # at HVN = resistance to movement

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Volume Profile", vote, abs(score), 0.74, {
        "poc": round(poc, 5), "at_hvn": bool(at_hvn), "at_lvn": bool(at_lvn),
        "price_above_poc": price > poc,
    })


def analyze_auction_market_theory(df: pd.DataFrame) -> SchoolResult:
    """School 48 — Auction Market Theory: balance vs imbalance, initiative vs responsive."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 20:
        return SchoolResult("Auction Market Theory", Vote.NEUTRAL, 0.3, 0.5, {})

    # Balance: market rotating in a range (low volatility, mean-reverting)
    # Imbalance: directional move with conviction
    price_range_20 = np.max(high[-20:]) - np.min(low[-20:])
    price_range_5 = np.max(high[-5:]) - np.min(low[-5:])
    avg_atr = float(np.nanmean(atr(high, low, close, 14)[-20:]))

    range_ratio = safe_div(price_range_5, price_range_20)
    balance = range_ratio < 0.35  # recent range small vs total = balanced
    imbalance = range_ratio > 0.6

    # Value area migration: is price moving away from recent value?
    price = close[-1]
    mean_price = np.mean(close[-20:])
    z_score = safe_div(price - mean_price, np.std(close[-20:]) + 1e-10)

    # Initiative vs responsive activity
    recent_vol_avg = np.mean(volume[-5:])
    prior_vol_avg = np.mean(volume[-20:-5])
    initiative = recent_vol_avg > prior_vol_avg * 1.2  # initiative = above avg volume

    score = 0.0
    if imbalance:
        score = 0.5 * np.sign(close[-1] - close[-5])
    if initiative:
        score *= 1.3
    score += z_score * 0.1

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Auction Market Theory", vote, abs(score), 0.70, {
        "market_balance": bool(balance),
        "market_imbalance": bool(imbalance),
        "initiative_activity": bool(initiative),
        "z_score": round(float(z_score), 3),
        "range_ratio": round(float(range_ratio), 3),
    })


def analyze_footprint_delta(df: pd.DataFrame) -> SchoolResult:
    """School 49 — Footprint / Delta: bid-ask volume imbalance estimate."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 5:
        return SchoolResult("Footprint Delta", Vote.NEUTRAL, 0.3, 0.5, {})

    # Estimate bid vs ask volume from close position in bar (Tick Rule approximation)
    # Close near high = mostly ask-side volume (buying)
    # Close near low = mostly bid-side volume (selling)
    bar_pos = np.array([
        safe_div(close[i] - low[i], high[i] - low[i] + 1e-10)
        for i in range(n)
    ])
    ask_vol = volume * bar_pos
    bid_vol = volume * (1 - bar_pos)
    delta = ask_vol - bid_vol
    cum_delta = np.cumsum(delta)

    # Divergence: price rising but delta falling (hidden selling)
    lookback = min(20, n)
    price_trend = close[-1] - close[-lookback]
    delta_trend = cum_delta[-1] - cum_delta[-lookback]
    delta_divergence = (price_trend > 0 and delta_trend < 0) or (price_trend < 0 and delta_trend > 0)

    recent_delta = np.sum(delta[-5:])
    total_vol_5 = np.sum(volume[-5:])
    delta_pct = safe_div(recent_delta, total_vol_5 + 1e-10)

    score = float(np.clip(delta_pct, -1, 1))
    if delta_divergence:
        score *= -0.5   # divergence weakens signal

    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("Footprint Delta", vote, abs(score), 0.68, {
        "delta_5_bars": round(float(recent_delta), 2),
        "delta_pct": round(float(delta_pct), 3),
        "cumulative_delta": round(float(cum_delta[-1]), 2),
        "delta_divergence": bool(delta_divergence),
    })


def analyze_anchored_vwap(df: pd.DataFrame) -> SchoolResult:
    """School 50 — Anchored VWAP: VWAP from significant swing low and high."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 10:
        return SchoolResult("Anchored VWAP", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    hl2 = (high + low) / 2

    # Anchor 1: from significant low (most bullish anchor)
    anchor_low_idx = int(np.argmin(low[-min(n, 60):]))
    cum_tpv_bull = np.cumsum(hl2[anchor_low_idx:] * volume[anchor_low_idx:])
    cum_vol_bull = np.cumsum(volume[anchor_low_idx:])
    avwap_bull = safe_div(cum_tpv_bull[-1], cum_vol_bull[-1])

    # Anchor 2: from significant high (most bearish anchor)
    anchor_high_idx = int(np.argmax(high[-min(n, 60):]))
    cum_tpv_bear = np.cumsum(hl2[anchor_high_idx:] * volume[anchor_high_idx:])
    cum_vol_bear = np.cumsum(volume[anchor_high_idx:])
    avwap_bear = safe_div(cum_tpv_bear[-1], cum_vol_bear[-1])

    above_bull_avwap = price > avwap_bull
    above_bear_avwap = price > avwap_bear

    score = 0.0
    if above_bull_avwap:
        score += 0.4
    else:
        score -= 0.4
    if above_bear_avwap:
        score += 0.3
    else:
        score -= 0.3

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Anchored VWAP", vote, abs(score), 0.74, {
        "avwap_from_low": round(float(avwap_bull), 5),
        "avwap_from_high": round(float(avwap_bear), 5),
        "price_above_bull_avwap": bool(above_bull_avwap),
        "price_above_bear_avwap": bool(above_bear_avwap),
    })


def analyze_dark_pool(df: pd.DataFrame) -> SchoolResult:
    """School 51 — Dark Pool Levels: high-volume price clusters as hidden S/R."""
    close = df['close'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 20:
        return SchoolResult("Dark Pool Levels", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    # High volume nodes = dark pool print approximation
    avg_vol = np.mean(volume)
    high_vol_prices = close[volume > avg_vol * 2.0]

    if len(high_vol_prices) == 0:
        return SchoolResult("Dark Pool Levels", Vote.NEUTRAL, 0.3, 0.4, {"no_levels": True})

    # Find nearest dark pool level above and below
    above = high_vol_prices[high_vol_prices > price]
    below = high_vol_prices[high_vol_prices <= price]

    nearest_above = float(np.min(above)) if len(above) > 0 else price * 1.02
    nearest_below = float(np.max(below)) if len(below) > 0 else price * 0.98

    dist_above = safe_div(nearest_above - price, price)
    dist_below = safe_div(price - nearest_below, price)

    # Closer to support below = bullish (price holding above dark pool level)
    score = 0.0
    if dist_below < 0.003:  # sitting right on dark pool support
        score = 0.5
    elif dist_above < 0.003:  # hitting dark pool resistance
        score = -0.4
    else:
        score = (dist_above - dist_below) / max(dist_above + dist_below, 0.001) * 0.4

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Dark Pool Levels", vote, abs(score), 0.65, {
        "nearest_support": round(nearest_below, 5),
        "nearest_resistance": round(nearest_above, 5),
        "dist_to_support_pct": round(dist_below * 100, 3),
        "dist_to_resistance_pct": round(dist_above * 100, 3),
        "high_vol_nodes_count": int(len(high_vol_prices)),
    })


# ─── GROUP 4.6: MATHEMATICAL INDICATORS ──────────────────────────────────────

def analyze_trix(df: pd.DataFrame) -> SchoolResult:
    """School 52 — TRIX: triple-smoothed EMA rate of change."""
    close = df['close'].values
    n = len(close)
    if n < 45:
        return SchoolResult("TRIX", Vote.NEUTRAL, 0.3, 0.5, {})

    period = 15
    e1 = ema(close, period)
    e2 = ema(e1, period)
    e3 = ema(e2, period)
    trix = np.full(n, np.nan)
    for i in range(1, n):
        if not np.isnan(e3[i]) and not np.isnan(e3[i-1]) and e3[i-1] != 0:
            trix[i] = (e3[i] - e3[i-1]) / e3[i-1] * 100

    signal = sma(trix, 9)
    cur_trix = trix[-1] if not np.isnan(trix[-1]) else 0
    cur_sig = signal[-1] if not np.isnan(signal[-1]) else 0
    prev_trix = trix[-2] if not np.isnan(trix[-2]) else 0
    prev_sig = signal[-2] if not np.isnan(signal[-2]) else 0

    bull_cross = prev_trix < prev_sig and cur_trix > cur_sig
    bear_cross = prev_trix > prev_sig and cur_trix < cur_sig

    score = 0.0
    if cur_trix > 0:
        score += 0.35
    else:
        score -= 0.35
    if cur_trix > cur_sig:
        score += 0.25
    else:
        score -= 0.25
    if bull_cross:
        score += 0.3
    if bear_cross:
        score -= 0.3

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("TRIX", vote, abs(score), 0.76, {
        "trix": round(float(cur_trix), 5),
        "signal": round(float(cur_sig), 5),
        "bullish_cross": bull_cross, "bearish_cross": bear_cross,
    })


def analyze_awesome_oscillator(df: pd.DataFrame) -> SchoolResult:
    """School 53 — Awesome Oscillator: SMA(5,hl2) - SMA(34,hl2)."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 34:
        return SchoolResult("Awesome Oscillator", Vote.NEUTRAL, 0.3, 0.5, {})

    hl2 = (high + low) / 2.0
    ao = sma(hl2, 5) - sma(hl2, 34)
    cur = ao[-1]; prev = ao[-2]; prev2 = ao[-3] if n > 3 else ao[-2]

    twin_peaks_bear = cur < 0 and prev < cur and prev < prev2 and prev2 < 0
    twin_peaks_bull = cur > 0 and prev > cur and prev > prev2 and prev2 > 0
    saucer_bull = cur > 0 and prev < cur and prev2 > prev
    zero_cross_bull = prev < 0 and cur > 0
    zero_cross_bear = prev > 0 and cur < 0

    score = 0.0
    if cur > 0:
        score += 0.35
    else:
        score -= 0.35
    if cur > prev:
        score += 0.2
    else:
        score -= 0.2
    if zero_cross_bull:
        score += 0.3
    if zero_cross_bear:
        score -= 0.3
    if saucer_bull:
        score += 0.2
    if twin_peaks_bear:
        score -= 0.2

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Awesome Oscillator", vote, abs(score), 0.74, {
        "ao": round(float(cur), 5),
        "zero_cross_bull": zero_cross_bull, "zero_cross_bear": zero_cross_bear,
        "saucer_bull": saucer_bull, "twin_peaks_bear": twin_peaks_bear,
    })


def analyze_ultimate_oscillator(df: pd.DataFrame) -> SchoolResult:
    """School 54 — Ultimate Oscillator: weighted 7/14/28 buying pressure."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 30:
        return SchoolResult("Ultimate Oscillator", Vote.NEUTRAL, 0.3, 0.5, {})

    bp = np.zeros(n)  # buying pressure
    tr_arr = np.zeros(n)
    for i in range(1, n):
        pc = close[i-1]
        bp[i] = close[i] - min(low[i], pc)
        tr_arr[i] = max(high[i], pc) - min(low[i], pc)

    def avg(length):
        if n < length:
            return 0.5
        return safe_div(np.sum(bp[-length:]), np.sum(tr_arr[-length:]) + 1e-10)

    a7 = avg(7); a14 = avg(14); a28 = avg(28)
    uo = 100 * (4 * a7 + 2 * a14 + a28) / 7

    score = 0.0
    if uo < 30:
        score = (30 - uo) / 30
    elif uo > 70:
        score = -(uo - 70) / 30
    else:
        score = (uo - 50) / 50 * 0.5

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("Ultimate Oscillator", vote, abs(score), 0.75, {
        "uo": round(float(uo), 2),
        "avg7": round(float(a7), 3), "avg14": round(float(a14), 3), "avg28": round(float(a28), 3),
        "overbought": uo > 70, "oversold": uo < 30,
    })


def analyze_roc(df: pd.DataFrame) -> SchoolResult:
    """School 55 — Rate of Change (ROC / Momentum Oscillator)."""
    close = df['close'].values
    n = len(close)
    if n < 15:
        return SchoolResult("ROC", Vote.NEUTRAL, 0.3, 0.5, {})

    periods = [9, 14, 21]
    scores = []
    details = {}
    for p in periods:
        if n > p:
            r = safe_div(close[-1] - close[-p-1], close[-p-1]) * 100
            details[f"roc{p}"] = round(float(r), 3)
            scores.append(np.sign(r) * min(1.0, abs(r) / 2))

    score = float(np.mean(scores)) if scores else 0.0
    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("ROC", vote, abs(score), 0.72, details)


def analyze_chaikin_money_flow(df: pd.DataFrame) -> SchoolResult:
    """School 56 — Chaikin Money Flow (CMF)."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 21:
        return SchoolResult("Chaikin Money Flow", Vote.NEUTRAL, 0.3, 0.5, {})

    period = 20
    mfm = np.array([
        safe_div((close[i] - low[i]) - (high[i] - close[i]), high[i] - low[i] + 1e-10)
        for i in range(n)
    ])
    mfv = mfm * volume
    cmf = safe_div(np.sum(mfv[-period:]), np.sum(volume[-period:]) + 1e-10)

    score = float(np.clip(cmf * 2, -1, 1))
    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("Chaikin Money Flow", vote, abs(score), 0.74, {
        "cmf": round(float(cmf), 4),
        "bullish": cmf > 0.05, "bearish": cmf < -0.05,
    })


def analyze_force_index(df: pd.DataFrame) -> SchoolResult:
    """School 57 — Force Index: price change × volume."""
    close = df['close'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 15:
        return SchoolResult("Force Index", Vote.NEUTRAL, 0.3, 0.5, {})

    fi = np.array([(close[i] - close[i-1]) * volume[i] for i in range(1, n)])
    fi2 = ema(fi, 2)
    fi13 = ema(fi, 13)
    cur2 = fi2[-1]; cur13 = fi13[-1]

    # Normalize by recent max
    max_fi = np.max(np.abs(fi[-20:])) + 1e-10
    score = float(np.clip(safe_div(cur13, max_fi), -1, 1))

    # Short-term reversal from fi2
    if abs(cur2) > max_fi * 0.5 and np.sign(cur2) != np.sign(cur13):
        score *= 0.5  # conflicting signals

    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("Force Index", vote, abs(score), 0.71, {
        "fi2": round(float(cur2), 2),
        "fi13": round(float(cur13), 2),
        "bullish": cur13 > 0,
    })


def analyze_vortex(df: pd.DataFrame) -> SchoolResult:
    """School 58 — Vortex Indicator: VI+ vs VI-."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 15:
        return SchoolResult("Vortex", Vote.NEUTRAL, 0.3, 0.5, {})

    period = 14
    tr_arr = np.array([
        max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
        for i in range(1, n)
    ])
    vm_plus = np.abs(high[1:] - low[:-1])
    vm_minus = np.abs(low[1:] - high[:-1])

    if len(tr_arr) < period:
        return SchoolResult("Vortex", Vote.NEUTRAL, 0.3, 0.5, {})

    vi_plus = safe_div(np.sum(vm_plus[-period:]), np.sum(tr_arr[-period:]) + 1e-10)
    vi_minus = safe_div(np.sum(vm_minus[-period:]), np.sum(tr_arr[-period:]) + 1e-10)
    diff = vi_plus - vi_minus

    score = float(np.clip(diff * 2, -1, 1))
    vote = Vote.BUY if score > 0.1 else (Vote.SELL if score < -0.1 else Vote.NEUTRAL)
    return SchoolResult("Vortex", vote, abs(score), 0.73, {
        "vi_plus": round(float(vi_plus), 4),
        "vi_minus": round(float(vi_minus), 4),
        "bullish": vi_plus > vi_minus,
    })


def analyze_supertrend(df: pd.DataFrame) -> SchoolResult:
    """School 59 — Supertrend: ATR-based trend direction indicator."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Supertrend", Vote.NEUTRAL, 0.3, 0.5, {})

    period = 10
    multiplier = 3.0
    atr_vals = atr(high, low, close, period)
    hl2 = (high + low) / 2.0

    upper_band = np.full(n, np.nan)
    lower_band = np.full(n, np.nan)
    supertrend = np.full(n, np.nan)
    direction = np.zeros(n)  # 1 = bullish, -1 = bearish

    for i in range(period, n):
        if np.isnan(atr_vals[i]):
            continue
        basic_upper = hl2[i] + multiplier * atr_vals[i]
        basic_lower = hl2[i] - multiplier * atr_vals[i]

        if not np.isnan(upper_band[i-1]):
            upper_band[i] = basic_upper if basic_upper < upper_band[i-1] or close[i-1] > upper_band[i-1] else upper_band[i-1]
        else:
            upper_band[i] = basic_upper

        if not np.isnan(lower_band[i-1]):
            lower_band[i] = basic_lower if basic_lower > lower_band[i-1] or close[i-1] < lower_band[i-1] else lower_band[i-1]
        else:
            lower_band[i] = basic_lower

        if not np.isnan(supertrend[i-1]):
            if supertrend[i-1] == upper_band[i-1]:
                direction[i] = -1 if close[i] > upper_band[i] else 1  # flip to bull if breaks upper
                # actually: if prev was upper (bearish) and price > upper -> flip bullish
                if close[i] > upper_band[i]:
                    supertrend[i] = lower_band[i]
                    direction[i] = 1
                else:
                    supertrend[i] = upper_band[i]
                    direction[i] = -1
            else:
                if close[i] < lower_band[i]:
                    supertrend[i] = upper_band[i]
                    direction[i] = -1
                else:
                    supertrend[i] = lower_band[i]
                    direction[i] = 1
        else:
            supertrend[i] = lower_band[i]
            direction[i] = 1

    cur_dir = direction[-1]
    st_val = supertrend[-1] if not np.isnan(supertrend[-1]) else close[-1]
    price = close[-1]
    dist = safe_div(abs(price - st_val), price)

    score = 0.7 * cur_dir
    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Supertrend", vote, abs(score), 0.80, {
        "supertrend": round(float(st_val), 5),
        "direction": "bullish" if cur_dir == 1 else "bearish",
        "price_vs_supertrend": "above" if price > st_val else "below",
        "distance_pct": round(dist * 100, 3),
    })


def analyze_stochastic_rsi(df: pd.DataFrame) -> SchoolResult:
    """School 60 — Stochastic RSI: RSI's RSI for overbought/oversold."""
    close = df['close'].values
    n = len(close)
    if n < 30:
        return SchoolResult("Stochastic RSI", Vote.NEUTRAL, 0.3, 0.5, {})

    rsi_vals = rsi(close, 14)
    period = 14
    stoch_rsi = np.full(n, np.nan)
    for i in range(period + 13, n):
        window = rsi_vals[i - period + 1:i + 1]
        window = window[~np.isnan(window)]
        if len(window) < period:
            continue
        min_r = np.min(window)
        max_r = np.max(window)
        stoch_rsi[i] = safe_div(rsi_vals[i] - min_r, max_r - min_r) * 100

    k = sma(stoch_rsi, 3)
    d = sma(k, 3)
    k_cur = k[-1] if not np.isnan(k[-1]) else 50
    d_cur = d[-1] if not np.isnan(d[-1]) else 50
    k_prev = k[-2] if not np.isnan(k[-2]) else 50
    d_prev = d[-2] if not np.isnan(d[-2]) else 50

    bull_cross = k_prev < d_prev and k_cur > d_cur and k_cur < 20
    bear_cross = k_prev > d_prev and k_cur < d_cur and k_cur > 80

    score = 0.0
    if k_cur < 20:
        score = (20 - k_cur) / 20
    elif k_cur > 80:
        score = -(k_cur - 80) / 20
    else:
        score = (k_cur - 50) / 100
    if bull_cross:
        score += 0.3
    if bear_cross:
        score -= 0.3

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Stochastic RSI", vote, abs(score), 0.77, {
        "stoch_rsi_k": round(float(k_cur), 2),
        "stoch_rsi_d": round(float(d_cur), 2),
        "overbought": k_cur > 80, "oversold": k_cur < 20,
        "bullish_cross": bull_cross, "bearish_cross": bear_cross,
    })


def analyze_fisher_transform(df: pd.DataFrame) -> SchoolResult:
    """School 61 — Fisher Transform: normalizes price into Gaussian distribution."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 12:
        return SchoolResult("Fisher Transform", Vote.NEUTRAL, 0.3, 0.5, {})

    period = 10
    fisher = np.full(n, np.nan)
    trigger = np.full(n, np.nan)

    for i in range(period - 1, n):
        h = np.max(high[i - period + 1:i + 1])
        l = np.min(low[i - period + 1:i + 1])
        value = safe_div(2 * ((close[i] - l) / (h - l + 1e-10)) - 1, 1)
        value = max(-0.999, min(0.999, value))
        fisher[i] = 0.5 * np.log((1 + value) / (1 - value))
        if i > period - 1 and not np.isnan(fisher[i-1]):
            trigger[i] = fisher[i-1]

    cur_f = fisher[-1] if not np.isnan(fisher[-1]) else 0
    cur_t = trigger[-1] if not np.isnan(trigger[-1]) else 0
    prev_f = fisher[-2] if not np.isnan(fisher[-2]) else 0
    prev_t = trigger[-2] if not np.isnan(trigger[-2]) else 0

    bull_cross = prev_f < prev_t and cur_f > cur_t
    bear_cross = prev_f > prev_t and cur_f < cur_t

    score = float(np.clip(cur_f * 0.5, -1, 1))
    if bull_cross:
        score = 0.7
    elif bear_cross:
        score = -0.7

    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Fisher Transform", vote, abs(score), 0.75, {
        "fisher": round(float(cur_f), 4),
        "trigger": round(float(cur_t), 4),
        "bullish_cross": bull_cross, "bearish_cross": bear_cross,
    })


def analyze_mass_index(df: pd.DataFrame) -> SchoolResult:
    """School 62 — Mass Index: reversal bulge detection in H-L range."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 30:
        return SchoolResult("Mass Index", Vote.NEUTRAL, 0.3, 0.5, {})

    hl = high - low
    ema9 = ema(hl, 9)
    ema9_9 = ema(ema9, 9)
    ratio = np.array([safe_div(ema9[i], ema9_9[i] + 1e-10) for i in range(n)])
    mi = np.full(n, np.nan)
    for i in range(24, n):
        mi[i] = np.sum(ratio[i - 24:i + 1])

    cur_mi = mi[-1] if not np.isnan(mi[-1]) else 26
    prev_mi = mi[-2] if not np.isnan(mi[-2]) else 26

    # Reversal bulge: MI rises above 27, then falls below 26.5
    bulge_reversal = cur_mi < 26.5 and prev_mi >= 27

    score = 0.0
    if bulge_reversal:
        # Determine direction from price trend
        trend = close[-1] - close[-10]
        score = -0.6 * np.sign(trend)  # reversal against trend
    elif cur_mi > 27:
        score = 0.0  # building bulge, neutral
    else:
        score = (close[-1] - close[-5]) / (np.std(close[-20:]) + 1e-10) * 0.15

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Mass Index", vote, abs(score), 0.68, {
        "mass_index": round(float(cur_mi), 3),
        "bulge_reversal": bulge_reversal,
        "above_27": cur_mi > 27,
    })


# ─── GROUP 4.7: SACRED GEOMETRY / ADVANCED GEOMETRY ─────────────────────────

def analyze_wolfe_waves(df: pd.DataFrame) -> SchoolResult:
    """School 63 — Wolfe Waves: 5-point pattern targeting EPA line."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 30:
        return SchoolResult("Wolfe Waves", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    # Find 5 pivot points for Wolfe Wave (alternating highs and lows)
    pivots = []
    for i in range(2, min(n-2, 25)):
        if high[i] > high[i-1] and high[i] > high[i-2] and high[i] > high[i+1] and high[i] > high[i+2]:
            pivots.append(('high', i, high[i]))
        elif low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i+1] and low[i] < low[i+2]:
            pivots.append(('low', i, low[i]))

    # Need at least 5 alternating pivots
    bullish_wolfe = False
    bearish_wolfe = False
    epa_price = price

    if len(pivots) >= 5:
        p1, p2, p3, p4, p5 = pivots[-5], pivots[-4], pivots[-3], pivots[-2], pivots[-1]
        # Bullish Wolfe: descending wedge — p1 high, p2 low, p3 high, p4 low, p5 (breakdown below p2)
        if p1[0] == 'high' and p2[0] == 'low' and p3[0] == 'high' and p4[0] == 'low':
            if p3[2] < p1[2] and p4[2] < p2[2]:  # lower highs, lower lows
                if price <= p4[2] * 1.005:
                    bullish_wolfe = True
                    # EPA: line from p1 to p4 extended
                    slope_epa = safe_div(p4[2] - p1[2], p4[1] - p1[1])
                    epa_price = p1[2] + slope_epa * (n - 1 - p1[1])

        # Bearish Wolfe: ascending wedge
        if p1[0] == 'low' and p2[0] == 'high' and p3[0] == 'low' and p4[0] == 'high':
            if p3[2] > p1[2] and p4[2] > p2[2]:
                if price >= p4[2] * 0.995:
                    bearish_wolfe = True

    score = 0.0
    if bullish_wolfe:
        score = 0.75
    elif bearish_wolfe:
        score = -0.75

    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Wolfe Waves", vote, abs(score), 0.67, {
        "bullish_pattern": bullish_wolfe,
        "bearish_pattern": bearish_wolfe,
        "epa_target": round(float(epa_price), 5),
        "pivots_found": len(pivots),
    })


def analyze_sacred_geometry(df: pd.DataFrame) -> SchoolResult:
    """School 64 — Sacred Geometry: phi ratios, golden spiral S/R levels."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Sacred Geometry", Vote.NEUTRAL, 0.3, 0.5, {})

    phi = 1.6180339887
    price = close[-1]
    swing_high = np.max(high[-min(n, 50):])
    swing_low = np.min(low[-min(n, 50):])
    swing = swing_high - swing_low

    # Sacred geometry levels from swing
    levels = {
        "phi_1": swing_low + swing / phi,
        "phi_2": swing_low + swing * (phi - 1),
        "phi_sq": swing_low + swing / (phi ** 2),
        "phi_cu": swing_low + swing / (phi ** 3),
    }

    tolerance = swing * 0.01
    at_support = any(abs(price - v) < tolerance and price >= v for v in levels.values())
    at_resistance = any(abs(price - v) < tolerance and price <= v for v in levels.values())

    # Find nearest level
    dists = {k: price - v for k, v in levels.items()}
    nearest_below = max((v for v in levels.values() if v <= price), default=swing_low)
    nearest_above = min((v for v in levels.values() if v > price), default=swing_high)
    dist_below = safe_div(price - nearest_below, price)
    dist_above = safe_div(nearest_above - price, price)

    score = 0.0
    if at_support:
        score = 0.5
    elif at_resistance:
        score = -0.5
    else:
        score = (dist_above - dist_below) / max(dist_above + dist_below, 0.001) * 0.4

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("Sacred Geometry", vote, abs(score), 0.60, {
        **{k: round(v, 5) for k, v in levels.items()},
        "at_phi_support": at_support,
        "at_phi_resistance": at_resistance,
        "nearest_support": round(float(nearest_below), 5),
        "nearest_resistance": round(float(nearest_above), 5),
    })


# ─── GROUP 4.8: ALTERNATIVE CHART TYPES ──────────────────────────────────────

def analyze_heikin_ashi(df: pd.DataFrame) -> SchoolResult:
    """School 65 — Heikin-Ashi: smoothed candles for trend clarity."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    open_ = df['open'].values if 'open' in df.columns else close.copy()
    n = len(close)
    if n < 5:
        return SchoolResult("Heikin-Ashi", Vote.NEUTRAL, 0.3, 0.5, {})

    ha_close = (open_ + high + low + close) / 4
    ha_open = np.zeros(n)
    ha_open[0] = (open_[0] + close[0]) / 2
    for i in range(1, n):
        ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2
    ha_high = np.maximum(high, np.maximum(ha_open, ha_close))
    ha_low = np.minimum(low, np.minimum(ha_open, ha_close))

    # Count consecutive bullish/bearish HA candles
    ha_bull = ha_close > ha_open
    consecutive_bull = 0
    consecutive_bear = 0
    for i in range(n-1, max(n-10, -1), -1):
        if ha_bull[i]:
            consecutive_bull += 1
        else:
            break
    for i in range(n-1, max(n-10, -1), -1):
        if not ha_bull[i]:
            consecutive_bear += 1
        else:
            break

    # No lower wicks on bullish HA = strong uptrend
    no_lower_wick = ha_low[-1] == min(ha_open[-1], ha_close[-1])
    no_upper_wick = ha_high[-1] == max(ha_open[-1], ha_close[-1])

    score = 0.0
    if consecutive_bull > 0:
        score += min(0.8, consecutive_bull * 0.15)
    if consecutive_bear > 0:
        score -= min(0.8, consecutive_bear * 0.15)
    if no_lower_wick and score > 0:
        score += 0.15
    if no_upper_wick and score < 0:
        score -= 0.15

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Heikin-Ashi", vote, abs(score), 0.76, {
        "consecutive_bullish": consecutive_bull,
        "consecutive_bearish": consecutive_bear,
        "no_lower_wick": bool(no_lower_wick),
        "ha_close": round(float(ha_close[-1]), 5),
        "ha_open": round(float(ha_open[-1]), 5),
    })


def analyze_renko(df: pd.DataFrame) -> SchoolResult:
    """School 66 — Renko: brick-based trend filter."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Renko", Vote.NEUTRAL, 0.3, 0.5, {})

    atr_val = float(np.nanmean(atr(high, low, close, 14)[-20:]))
    brick = atr_val  # ATR-based brick size

    bricks = []
    current = close[0]
    for price in close[1:]:
        while price >= current + brick:
            bricks.append(1)   # bullish brick
            current += brick
        while price <= current - brick:
            bricks.append(-1)  # bearish brick
            current -= brick

    if not bricks:
        return SchoolResult("Renko", Vote.NEUTRAL, 0.3, 0.5, {"brick_size": round(brick, 5)})

    # Count consecutive same-direction bricks
    last_dir = bricks[-1]
    streak = 0
    for b in reversed(bricks):
        if b == last_dir:
            streak += 1
        else:
            break

    score = float(np.clip(last_dir * min(1.0, streak * 0.2), -1, 1))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Renko", vote, abs(score), 0.74, {
        "brick_size": round(brick, 5),
        "total_bricks": len(bricks),
        "current_direction": "bullish" if last_dir == 1 else "bearish",
        "consecutive_streak": streak,
    })


def analyze_kagi(df: pd.DataFrame) -> SchoolResult:
    """School 67 — Kagi Charts: shoulder/waist transitions, Yang/Yin lines."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Kagi", Vote.NEUTRAL, 0.3, 0.5, {})

    atr_val = float(np.nanmean(atr(high, low, close, 14)[-20:])) * 0.4
    reversal = atr_val

    # Build Kagi lines
    lines = []  # (direction, level)
    direction = 1 if close[-1] > close[0] else -1
    last_level = close[0]

    for price in close[1:]:
        if direction == 1:
            if price > last_level:
                last_level = price
            elif price < last_level - reversal:
                lines.append((1, last_level))
                direction = -1
                last_level = price
        else:
            if price < last_level:
                last_level = price
            elif price > last_level + reversal:
                lines.append((-1, last_level))
                direction = 1
                last_level = price

    # Yang line (bullish): current Kagi line is going up
    yang = direction == 1
    # Recent reversals
    recent_lines = lines[-4:] if len(lines) >= 4 else lines
    bull_count = sum(1 for d, _ in recent_lines if d == 1)
    bear_count = len(recent_lines) - bull_count

    score = 0.5 if yang else -0.5
    score += (bull_count - bear_count) / max(len(recent_lines), 1) * 0.3

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Kagi", vote, abs(score), 0.70, {
        "line_type": "Yang (bullish)" if yang else "Yin (bearish)",
        "reversals_count": len(lines),
        "recent_bull_lines": bull_count,
        "recent_bear_lines": bear_count,
    })


# ─── GROUP 4.9: QUANTITATIVE / SYSTEMATIC ────────────────────────────────────

def analyze_mean_reversion(df: pd.DataFrame) -> SchoolResult:
    """School 68 — Mean Reversion: Z-score and Bollinger %B reversion signals."""
    close = df['close'].values
    n = len(close)
    if n < 20:
        return SchoolResult("Mean Reversion", Vote.NEUTRAL, 0.3, 0.5, {})

    period = 20
    mean = np.mean(close[-period:])
    std = np.std(close[-period:])
    price = close[-1]
    z = safe_div(price - mean, std + 1e-10)

    # Half-life of mean reversion (AR(1) estimation)
    y = close[-period:]
    y_lag = close[-period-1:-1]
    if len(y) == len(y_lag) and np.std(y_lag) > 0:
        beta = np.cov(y, y_lag)[0, 1] / np.var(y_lag)
        half_life = -np.log(2) / np.log(abs(beta)) if abs(beta) < 1 and beta != 0 else 999
    else:
        half_life = 999

    # Strong reversion signal when |z| > 2
    score = 0.0
    if z < -2.0:
        score = min(1.0, abs(z) / 3)      # oversold, buy
    elif z > 2.0:
        score = -min(1.0, abs(z) / 3)     # overbought, sell
    elif z < -1.5:
        score = 0.4
    elif z > 1.5:
        score = -0.4

    # Reduce confidence if half-life is too long (not mean-reverting)
    confidence = 0.80 if half_life < 20 else 0.55

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Mean Reversion", vote, abs(score), confidence, {
        "z_score": round(float(z), 3),
        "mean": round(float(mean), 5),
        "std": round(float(std), 5),
        "half_life_bars": round(float(half_life), 1),
        "strong_signal": abs(z) > 2.0,
    })


def analyze_canslim(df: pd.DataFrame) -> SchoolResult:
    """School 69 — CANSLIM: momentum + relative strength screening proxy."""
    close = df['close'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 50:
        return SchoolResult("CANSLIM", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    # RS Rating proxy: 12-month return (use available data)
    lookback = min(n - 1, 252)
    rs = safe_div(price - close[-lookback - 1], close[-lookback - 1]) * 100

    # Price near 52-week high
    high_52w = np.max(close[-min(n, 252):])
    pct_from_high = safe_div(price - high_52w, high_52w) * 100

    # Volume: above average on up-moves (institutional buying)
    avg_vol = np.mean(volume[-50:])
    recent_up_vol = np.mean(volume[-5:][close[-5:] > np.roll(close, 1)[-5:]])
    vol_on_up = safe_div(recent_up_vol, avg_vol)

    # Cup with handle: price near prior high after pullback
    cup_high = np.max(close[-30:])
    cup_low = np.min(close[-30:])
    handle_depth = safe_div(cup_high - price, cup_high - cup_low)
    cup_pattern = 0.0 < handle_depth < 0.15 and price > cup_high * 0.95

    score = 0.0
    if rs > 0:
        score += min(0.4, rs / 100)
    else:
        score += max(-0.4, rs / 100)
    if pct_from_high > -10:
        score += 0.2
    if vol_on_up > 1.2:
        score += 0.2
    if cup_pattern:
        score += 0.25

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.3 else (Vote.SELL if score < -0.1 else Vote.NEUTRAL)
    return SchoolResult("CANSLIM", vote, abs(score), 0.68, {
        "rs_rating_pct": round(float(rs), 2),
        "pct_from_52w_high": round(float(pct_from_high), 2),
        "vol_on_up_ratio": round(float(vol_on_up), 2),
        "cup_with_handle": bool(cup_pattern),
    })


def analyze_momentum_trading(df: pd.DataFrame) -> SchoolResult:
    """School 70 — Momentum Trading: cross-sectional and time-series momentum."""
    close = df['close'].values
    volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
    n = len(close)
    if n < 30:
        return SchoolResult("Momentum Trading", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    # Time-series momentum: returns over multiple horizons
    horizons = [5, 10, 21]
    mom_scores = []
    details = {}
    for h in horizons:
        if n > h:
            ret = safe_div(price - close[-h-1], close[-h-1])
            details[f"mom_{h}d"] = round(ret * 100, 3)
            mom_scores.append(np.sign(ret) * min(1.0, abs(ret) * 20))

    # 52-week momentum
    if n > 252:
        ret252 = safe_div(price - close[-253], close[-253])
        details["mom_252d"] = round(ret252 * 100, 2)
        mom_scores.append(np.sign(ret252) * min(0.5, abs(ret252) * 5))

    # Volume-weighted momentum
    vw_close = close * volume
    vwm = safe_div(np.sum(vw_close[-10:]), np.sum(volume[-10:]) + 1e-10)
    above_vwm = price > vwm

    score = float(np.mean(mom_scores)) if mom_scores else 0.0
    if above_vwm:
        score += 0.1
    else:
        score -= 0.1

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Momentum Trading", vote, abs(score), 0.76, {
        **details, "above_vwma": bool(above_vwm),
    })


# ─── GROUP 4.10: TIME ANALYSIS ────────────────────────────────────────────────

def analyze_fibonacci_time_zones(df: pd.DataFrame) -> SchoolResult:
    """School 71 — Fibonacci Time Zones: time-based Fib projections."""
    close = df['close'].values
    n = len(close)
    if n < 21:
        return SchoolResult("Fibonacci Time Zones", Vote.NEUTRAL, 0.3, 0.5, {})

    fib_seq = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    # Anchor from the most recent significant swing
    # Find the pivot (max swing in last 50 bars)
    lookback = min(n, 50)
    swing_start = n - lookback
    fib_zones = [swing_start + f for f in fib_seq if swing_start + f < n + 5]

    # Is current bar at or near a Fibonacci time zone?
    current_bar = n - 1
    at_fib_zone = any(abs(current_bar - z) <= 1 for z in fib_zones)

    # Trend direction to determine zone significance
    price_trend = close[-1] - close[-min(n, 21)]

    score = 0.0
    if at_fib_zone:
        if price_trend > 0:
            score = 0.4   # at Fib time zone in uptrend = potential continuation
        else:
            score = -0.4
    else:
        score = (price_trend / (np.std(close[-20:]) + 1e-10)) * 0.1
        score = max(-0.3, min(0.3, score))

    next_zone = next((z for z in sorted(fib_zones) if z > current_bar), current_bar + 21)
    bars_to_next = next_zone - current_bar

    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("Fibonacci Time Zones", vote, abs(score), 0.60, {
        "at_fib_time_zone": bool(at_fib_zone),
        "bars_to_next_zone": int(bars_to_next),
        "active_zones": [int(z) for z in fib_zones[-3:]],
    })


def analyze_cyclic_time(df: pd.DataFrame) -> SchoolResult:
    """School 72 — Cyclic Time Analysis: spectral dominant cycle + phase."""
    close = df['close'].values
    n = len(close)
    if n < 40:
        return SchoolResult("Cyclic Time", Vote.NEUTRAL, 0.3, 0.4, {})

    # Detrend using linear regression
    x = np.arange(n)
    coeffs = np.polyfit(x, close, 1)
    detrended = close - np.polyval(coeffs, x)

    # FFT to find dominant cycle
    fft_vals = np.fft.rfft(detrended)
    freqs = np.fft.rfftfreq(n)
    power = np.abs(fft_vals) ** 2

    # Exclude DC and very high freq
    valid = (freqs > 0.02) & (freqs < 0.4)
    if not np.any(valid):
        return SchoolResult("Cyclic Time", Vote.NEUTRAL, 0.3, 0.4, {})

    dom_freq_idx = np.argmax(power[valid])
    dom_freq = freqs[valid][dom_freq_idx]
    dom_period = int(round(1.0 / dom_freq)) if dom_freq > 0 else 20

    # Phase within dominant cycle
    phase = (n % dom_period) / dom_period if dom_period > 0 else 0.5

    # 0.0-0.25 = ascending early (buy), 0.25-0.5 = ascending late (hold)
    # 0.5-0.75 = descending early (sell), 0.75-1.0 = descending late (buy soon)
    if phase < 0.25:
        score = 0.6
    elif phase < 0.5:
        score = 0.3
    elif phase < 0.75:
        score = -0.5
    else:
        score = -0.15

    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Cyclic Time", vote, abs(score), 0.62, {
        "dominant_period_bars": int(dom_period),
        "phase": round(float(phase), 3),
        "cycle_position": "early_ascent" if phase < 0.25 else
                          "late_ascent" if phase < 0.5 else
                          "early_descent" if phase < 0.75 else "late_descent",
    })


# ─── GROUP 4.11: CLASSICAL CHART PATTERNS ────────────────────────────────────

def analyze_classical_chart_patterns(df: pd.DataFrame) -> SchoolResult:
    """School 73 — Classical Chart Patterns: H&S, Double Top/Bottom, Triangles, Flags, Wedges."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    if n < 30:
        return SchoolResult("Classical Chart Patterns", Vote.NEUTRAL, 0.3, 0.5, {})

    price = close[-1]
    atr_val = float(np.nanmean(atr(high, low, close, 14)[-20:]))
    tol = atr_val * 0.5

    patterns_found = []
    score = 0.0

    # Double Bottom: two lows near same level, price now above neckline
    if n >= 20:
        lows_20 = low[-20:]
        min1_idx = np.argmin(lows_20)
        min1 = lows_20[min1_idx]
        remaining = np.concatenate([lows_20[:min1_idx], lows_20[min1_idx+1:]])
        min2 = np.min(remaining)
        neckline = np.max(high[-20:])
        if abs(min1 - min2) < tol and price > neckline - tol:
            patterns_found.append("double_bottom")
            score += 0.6

    # Double Top: two highs near same level
    if n >= 20 and not patterns_found:
        highs_20 = high[-20:]
        max1_idx = np.argmax(highs_20)
        max1 = highs_20[max1_idx]
        remaining = np.concatenate([highs_20[:max1_idx], highs_20[max1_idx+1:]])
        max2 = np.max(remaining)
        neckline_low = np.min(low[-20:])
        if abs(max1 - max2) < tol and price < neckline_low + tol:
            patterns_found.append("double_top")
            score -= 0.6

    # Head and Shoulders (simplified): 3 peaks, middle highest
    if n >= 30 and not patterns_found:
        highs_30 = high[-30:]
        peak1 = np.max(highs_30[:10])
        peak2 = np.max(highs_30[10:20])  # head
        peak3 = np.max(highs_30[20:])
        if peak2 > peak1 and peak2 > peak3 and abs(peak1 - peak3) < tol * 2:
            neckline_hs = np.min(low[-30:])
            if price < neckline_hs + tol:
                patterns_found.append("head_and_shoulders")
                score -= 0.7

    # Ascending Triangle: flat resistance, rising support
    if n >= 20 and not patterns_found:
        resistance = np.max(high[-20:])
        supports = low[-20:]
        support_slope = np.polyfit(np.arange(20), supports, 1)[0]
        at_resistance = abs(price - resistance) < tol
        if support_slope > 0 and at_resistance:
            patterns_found.append("ascending_triangle_breakout_pending")
            score += 0.4

    # Descending Triangle: flat support, falling resistance
    if n >= 20 and not patterns_found:
        support_flat = np.min(low[-20:])
        resist_vals = high[-20:]
        resist_slope = np.polyfit(np.arange(20), resist_vals, 1)[0]
        at_support = abs(price - support_flat) < tol
        if resist_slope < 0 and at_support:
            patterns_found.append("descending_triangle_breakout_pending")
            score -= 0.4

    # Flag: strong move followed by tight consolidation
    if n >= 15 and not patterns_found:
        impulse_move = abs(close[-15] - close[-10])
        consolidation_range = np.max(high[-5:]) - np.min(low[-5:])
        if impulse_move > 2 * atr_val and consolidation_range < 0.5 * atr_val:
            direction = np.sign(close[-10] - close[-15])
            patterns_found.append("flag")
            score += 0.5 * direction

    # Wedge rising (bearish) / falling (bullish)
    if n >= 20 and not patterns_found:
        high_slope = np.polyfit(np.arange(20), high[-20:], 1)[0]
        low_slope = np.polyfit(np.arange(20), low[-20:], 1)[0]
        if high_slope > 0 and low_slope > 0 and high_slope < low_slope:
            patterns_found.append("rising_wedge_bearish")
            score -= 0.5
        elif high_slope < 0 and low_slope < 0 and high_slope > low_slope:
            patterns_found.append("falling_wedge_bullish")
            score += 0.5

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Classical Chart Patterns", vote, abs(score), 0.72, {
        "patterns_found": patterns_found,
        "pattern_count": len(patterns_found),
        "atr": round(atr_val, 5),
    })


# ─── GROUP 4.12: EXTENDED CANDLESTICK PATTERNS ───────────────────────────────

def analyze_extended_candlesticks(df: pd.DataFrame) -> SchoolResult:
    """School 74 — Extended Candlesticks: Belt-Hold, Tri-Star, Breakaway, Mat Hold, Ladder."""
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    open_ = df['open'].values if 'open' in df.columns else close.copy()
    n = len(close)
    if n < 5:
        return SchoolResult("Extended Candlesticks", Vote.NEUTRAL, 0.3, 0.5, {})

    atr_val = float(np.nanmean(atr(high, low, close, 14)[-20:])) if n >= 20 else float(np.mean(high - low))

    def body(i): return abs(close[i] - open_[i])
    def wick_up(i): return high[i] - max(close[i], open_[i])
    def wick_dn(i): return min(close[i], open_[i]) - low[i]
    def bull(i): return close[i] > open_[i]
    def bear(i): return close[i] < open_[i]
    def doji(i): return body(i) < atr_val * 0.1

    patterns = []
    score = 0.0

    # Belt-Hold Bullish: long white candle opens at low (no lower wick)
    if n >= 1 and bull(-1) and wick_dn(-1) < atr_val * 0.05 and body(-1) > atr_val:
        patterns.append("belt_hold_bull"); score += 0.4

    # Belt-Hold Bearish: long black candle opens at high
    if n >= 1 and bear(-1) and wick_up(-1) < atr_val * 0.05 and body(-1) > atr_val:
        patterns.append("belt_hold_bear"); score -= 0.4

    # Tri-Star Bullish: three dojis in downtrend, middle gaps down
    if n >= 3 and doji(-1) and doji(-2) and doji(-3):
        if low[-2] < low[-3] and low[-2] < low[-1]:
            patterns.append("tri_star_bull"); score += 0.55
        elif high[-2] > high[-3] and high[-2] > high[-1]:
            patterns.append("tri_star_bear"); score -= 0.55

    # Breakaway Bullish: 5-candle pattern, first 3 bear, then bull escape
    if n >= 5:
        if (bear(-5) and bear(-4) and bear(-3) and
                open_[-4] < close[-5] and open_[-3] < close[-4] and  # gap downs
                bull(-1) and close[-1] > close[-3]):
            patterns.append("breakaway_bull"); score += 0.5
        if (bull(-5) and bull(-4) and bull(-3) and
                open_[-4] > close[-5] and open_[-3] > close[-4] and
                bear(-1) and close[-1] < close[-3]):
            patterns.append("breakaway_bear"); score -= 0.5

    # Mat Hold: bullish continuation (bull, 3 small bears, bull breakout)
    if n >= 5:
        if (bull(-5) and body(-5) > atr_val and
                all(bear(-i) and body(-i) < atr_val * 0.5 for i in range(2, 5)) and
                bull(-1) and close[-1] > close[-5]):
            patterns.append("mat_hold_bull"); score += 0.55

    # Ladder Bottom: 3 declining bears, 4th bear with upper wick, 5th bull
    if n >= 5:
        if (all(bear(-i) for i in range(2, 6)) and
                close[-5] > close[-4] > close[-3] > close[-2] and
                wick_up(-2) > body(-2) and bull(-1)):
            patterns.append("ladder_bottom"); score += 0.6

    # Stick Sandwich: two same-color candles around opposite
    if n >= 3:
        if bear(-3) and bull(-2) and bear(-1) and abs(close[-3] - close[-1]) < atr_val * 0.1:
            patterns.append("stick_sandwich_bull"); score += 0.4

    # Unique Three River Bottom: 3-candle reversal at bottom
    if n >= 3:
        if (bear(-3) and body(-3) > atr_val and
                bear(-2) and low[-2] < low[-3] and body(-2) < body(-3) and
                bull(-1) and close[-1] < open_[-2]):
            patterns.append("unique_three_river_bottom"); score += 0.5

    # Counterattack Lines Bullish: bear then bull, both close at same level
    if n >= 2:
        if bear(-2) and bull(-1) and abs(close[-2] - close[-1]) < atr_val * 0.15:
            patterns.append("counterattack_bull"); score += 0.35
        if bull(-2) and bear(-1) and abs(close[-2] - close[-1]) < atr_val * 0.15:
            patterns.append("counterattack_bear"); score -= 0.35

    if not patterns:
        score = (close[-1] - close[-2]) / (atr_val + 1e-10) * 0.1
        patterns.append("no_pattern")

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Extended Candlesticks", vote, abs(score), 0.70, {
        "patterns": patterns,
        "pattern_count": len([p for p in patterns if p != "no_pattern"]),
    })


# ─── EXTENDED MASTER ANALYZER ────────────────────────────────────────────────

EXTENDED_ANALYZERS = [
    analyze_dow_theory,            # 30
    analyze_ict_full,              # 31
    analyze_ipda,                  # 32
    analyze_liquidity_theory,      # 33
    analyze_naked_trading,         # 34
    analyze_order_flow,            # 35
    analyze_supply_demand_zones,   # 36
    analyze_andrews_pitchfork,     # 37
    analyze_point_figure,          # 38
    analyze_darvas_box,            # 39
    analyze_weinstein_stages,      # 40
    analyze_bill_williams,         # 41
    analyze_turtle_trading,        # 42
    analyze_trendlines_channels,   # 43
    analyze_hurst_cycles,          # 44
    analyze_kondratieff,           # 45
    analyze_market_profile,        # 46
    analyze_volume_profile,        # 47
    analyze_auction_market_theory, # 48
    analyze_footprint_delta,       # 49
    analyze_anchored_vwap,         # 50
    analyze_dark_pool,             # 51
    analyze_trix,                  # 52
    analyze_awesome_oscillator,    # 53
    analyze_ultimate_oscillator,   # 54
    analyze_roc,                   # 55
    analyze_chaikin_money_flow,    # 56
    analyze_force_index,           # 57
    analyze_vortex,                # 58
    analyze_supertrend,            # 59
    analyze_stochastic_rsi,        # 60
    analyze_fisher_transform,      # 61
    analyze_mass_index,            # 62
    analyze_wolfe_waves,           # 63
    analyze_sacred_geometry,       # 64
    analyze_heikin_ashi,           # 65
    analyze_renko,                 # 66
    analyze_kagi,                  # 67
    analyze_mean_reversion,        # 68
    analyze_canslim,               # 69
    analyze_momentum_trading,      # 70
    analyze_fibonacci_time_zones,  # 71
    analyze_cyclic_time,           # 72
    analyze_classical_chart_patterns,  # 73
    analyze_extended_candlesticks, # 74
]


def analyze_all_extended(df: pd.DataFrame) -> List[SchoolResult]:
    """Run all 45 extended schools (30–74) on the given OHLCV DataFrame."""
    if len(df) < 20:
        return []
    results = []
    for analyzer in EXTENDED_ANALYZERS:
        try:
            results.append(analyzer(df))
        except Exception:
            pass
    return results
