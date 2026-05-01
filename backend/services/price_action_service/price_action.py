"""Price Action Service — The Market Lion.
Detects: BOS (Break of Structure), CHoCH (Change of Character), FVG (Fair Value Gap),
Order Blocks (OB), Breaker Blocks, Mitigation Blocks, Premium/Discount arrays,
Liquidity Voids, Displacement candles. FastAPI + Redis caching.
"""
import asyncio
import logging
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as aioredis

logger = logging.getLogger("price-action-service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Price Action Service", version="1.0.0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/5")


# ─── Models ───────────────────────────────────────────────────────────────────

class StructureType(str, Enum):
    BOS_BULLISH    = "BOS_BULLISH"     # Break of Structure — bullish
    BOS_BEARISH    = "BOS_BEARISH"
    CHOCH_BULLISH  = "CHoCH_BULLISH"   # Change of Character — bullish
    CHOCH_BEARISH  = "CHoCH_BEARISH"
    HH = "HH"; HL = "HL"; LH = "LH"; LL = "LL"


class ZoneType(str, Enum):
    BULLISH_OB     = "BULLISH_OB"      # Order Block
    BEARISH_OB     = "BEARISH_OB"
    BREAKER_BULL   = "BREAKER_BULL"    # Breaker Block
    BREAKER_BEAR   = "BREAKER_BEAR"
    BULLISH_FVG    = "BULLISH_FVG"     # Fair Value Gap
    BEARISH_FVG    = "BEARISH_FVG"
    BULLISH_VOID   = "BULLISH_VOID"    # Liquidity void
    BEARISH_VOID   = "BEARISH_VOID"
    MITIGATION     = "MITIGATION"


@dataclass
class StructurePoint:
    type: StructureType
    bar_index: int
    price: float
    swing_high: float
    swing_low: float
    strength: float   # 0-1


@dataclass
class PriceZone:
    zone_type: ZoneType
    top: float
    bottom: float
    bar_index: int
    mitigated: bool
    mitigation_pct: float    # 0-1: how much of the zone has been retested
    strength: float          # based on displacement / ATR
    active: bool
    formed_by_close: bool


@dataclass
class PriceActionReport:
    asset: str
    timeframe: str
    # Structure
    trend: str              # BULLISH / BEARISH / RANGING
    last_bos: Optional[StructurePoint]
    last_choch: Optional[StructurePoint]
    swing_high: float
    swing_low: float
    # Premium / Discount
    equilibrium: float
    premium_zone: Tuple[float, float]
    discount_zone: Tuple[float, float]
    current_zone: str       # PREMIUM / DISCOUNT / EQUILIBRIUM
    # Active zones
    order_blocks: List[PriceZone]
    fvgs: List[PriceZone]
    breakers: List[PriceZone]
    voids: List[PriceZone]
    # Overall signal
    vote: str               # BUY / SELL / NEUTRAL
    score: float
    confidence: float
    generated_at: str


class OHLCVInput(BaseModel):
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: Optional[List[float]] = None


class PAScanRequest(BaseModel):
    asset: str
    timeframe: str
    ohlcv: OHLCVInput


# ─── Helpers ──────────────────────────────────────────────────────────────────

def safe_div(a: float, b: float, d: float = 0.0) -> float:
    return a / b if b != 0 else d


def calc_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
    if len(close) < period + 1:
        return float(np.mean(high - low))
    tr = np.maximum(high[1:] - low[1:],
         np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
    atr_arr = np.zeros(len(close))
    atr_arr[period] = np.mean(tr[:period])
    for i in range(period + 1, len(close)):
        atr_arr[i] = (atr_arr[i-1] * (period - 1) + tr[i-1]) / period
    return float(np.nanmean(atr_arr[-20:]))


def find_swing_pivots(high: np.ndarray, low: np.ndarray, left: int = 3, right: int = 3):
    """Returns list of (bar_idx, price, 'high'|'low') sorted by bar_idx."""
    n = len(high)
    pivots = []
    for i in range(left, n - right):
        if all(high[i] > high[i-j] for j in range(1, left+1)) and \
           all(high[i] > high[i+j] for j in range(1, right+1)):
            pivots.append((i, high[i], 'high'))
        elif all(low[i] < low[i-j] for j in range(1, left+1)) and \
             all(low[i] < low[i+j] for j in range(1, right+1)):
            pivots.append((i, low[i], 'low'))
    return pivots


# ─── Market Structure ─────────────────────────────────────────────────────────

def analyze_structure(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float
) -> Tuple[str, Optional[StructurePoint], Optional[StructurePoint], float, float, List]:
    """Identify HH/HL/LH/LL sequence, BOS, CHoCH."""
    pivots = find_swing_pivots(high, low, left=3, right=3)
    if len(pivots) < 4:
        swing_high = float(np.max(high[-20:]))
        swing_low = float(np.min(low[-20:]))
        return "RANGING", None, None, swing_high, swing_low, []

    structure_points = []
    last_bos: Optional[StructurePoint] = None
    last_choch: Optional[StructurePoint] = None

    swing_highs = [(i, p, t) for i, p, t in pivots if t == 'high']
    swing_lows  = [(i, p, t) for i, p, t in pivots if t == 'low']

    overall_swing_high = float(max(p for _, p, _ in swing_highs)) if swing_highs else float(np.max(high))
    overall_swing_low = float(min(p for _, p, _ in swing_lows)) if swing_lows else float(np.min(low))

    # Determine trend from sequence of swing highs/lows
    bullish_count = 0
    bearish_count = 0

    for i in range(1, min(len(swing_highs), 4)):
        if swing_highs[i][1] > swing_highs[i-1][1]:
            bullish_count += 1  # HH
        else:
            bearish_count += 1  # LH

    for i in range(1, min(len(swing_lows), 4)):
        if swing_lows[i][1] > swing_lows[i-1][1]:
            bullish_count += 1  # HL
        else:
            bearish_count += 1  # LL

    if bullish_count > bearish_count + 1:
        trend = "BULLISH"
    elif bearish_count > bullish_count + 1:
        trend = "BEARISH"
    else:
        trend = "RANGING"

    # BOS: price breaks beyond previous swing high (bullish) or low (bearish)
    price = close[-1]
    if len(swing_highs) >= 2:
        prev_high = swing_highs[-2][1]
        if price > prev_high:
            last_bos = StructurePoint(
                type=StructureType.BOS_BULLISH, bar_index=len(close) - 1,
                price=prev_high, swing_high=overall_swing_high, swing_low=overall_swing_low,
                strength=min(1.0, safe_div(price - prev_high, atr_val))
            )

    if len(swing_lows) >= 2:
        prev_low = swing_lows[-2][1]
        if price < prev_low:
            last_bos = StructurePoint(
                type=StructureType.BOS_BEARISH, bar_index=len(close) - 1,
                price=prev_low, swing_high=overall_swing_high, swing_low=overall_swing_low,
                strength=min(1.0, safe_div(prev_low - price, atr_val))
            )

    # CHoCH: change in structure direction
    if trend == "BULLISH" and len(swing_lows) >= 2 and swing_lows[-1][1] < swing_lows[-2][1]:
        last_choch = StructurePoint(
            type=StructureType.CHOCH_BEARISH, bar_index=swing_lows[-1][0],
            price=swing_lows[-1][1], swing_high=overall_swing_high, swing_low=overall_swing_low,
            strength=safe_div(swing_lows[-2][1] - swing_lows[-1][1], atr_val * 2),
        )
    elif trend == "BEARISH" and len(swing_highs) >= 2 and swing_highs[-1][1] > swing_highs[-2][1]:
        last_choch = StructurePoint(
            type=StructureType.CHOCH_BULLISH, bar_index=swing_highs[-1][0],
            price=swing_highs[-1][1], swing_high=overall_swing_high, swing_low=overall_swing_low,
            strength=safe_div(swing_highs[-1][1] - swing_highs[-2][1], atr_val * 2),
        )

    return trend, last_bos, last_choch, overall_swing_high, overall_swing_low, pivots


# ─── Order Blocks ─────────────────────────────────────────────────────────────

def find_order_blocks(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    atr_val: float, max_blocks: int = 5
) -> List[PriceZone]:
    """Order Blocks: last opposing candle before a strong displacement move."""
    n = len(close)
    blocks = []
    DISPLACEMENT = atr_val * 1.5

    for i in range(2, n - 1):
        # Bullish OB: bearish candle (i) followed by strong bullish displacement
        body_i = abs(close[i] - open_[i])
        is_bear = close[i] < open_[i]
        is_bull = close[i] > open_[i]

        if is_bear and body_i > atr_val * 0.3:
            # Check if next candle(s) displace upward
            displacement = close[min(i+2, n-1)] - high[i]
            if displacement > DISPLACEMENT:
                mitigated = any(low[j] <= close[i] for j in range(i+1, n))
                mit_pct = 0.0
                if mitigated:
                    for j in range(i+1, n):
                        if low[j] <= close[i]:
                            mit_pct = min(1.0, safe_div(close[i] - low[j], close[i] - open_[i]))
                            break
                blocks.append(PriceZone(
                    zone_type=ZoneType.BULLISH_OB,
                    top=open_[i], bottom=low[i],
                    bar_index=i, mitigated=mitigated,
                    mitigation_pct=mit_pct,
                    strength=min(1.0, displacement / (atr_val * 3)),
                    active=not mitigated,
                    formed_by_close=True,
                ))

        # Bearish OB: bullish candle (i) followed by strong bearish displacement
        if is_bull and body_i > atr_val * 0.3:
            displacement = low[i] - close[min(i+2, n-1)]
            if displacement > DISPLACEMENT:
                mitigated = any(high[j] >= close[i] for j in range(i+1, n))
                mit_pct = 0.0
                if mitigated:
                    for j in range(i+1, n):
                        if high[j] >= close[i]:
                            mit_pct = min(1.0, safe_div(high[j] - close[i], open_[i] - close[i]))
                            break
                blocks.append(PriceZone(
                    zone_type=ZoneType.BEARISH_OB,
                    top=high[i], bottom=open_[i],
                    bar_index=i, mitigated=mitigated,
                    mitigation_pct=mit_pct,
                    strength=min(1.0, displacement / (atr_val * 3)),
                    active=not mitigated,
                    formed_by_close=True,
                ))

    # Keep most recent + unmitigated
    active = [b for b in blocks if b.active]
    return sorted(active, key=lambda b: -b.bar_index)[:max_blocks]


# ─── Fair Value Gaps ──────────────────────────────────────────────────────────

def find_fvgs(
    high: np.ndarray, low: np.ndarray, close: np.ndarray,
    atr_val: float, max_fvgs: int = 8
) -> List[PriceZone]:
    """FVG: 3-candle pattern where candle 1 high < candle 3 low (bullish) or vice versa."""
    n = len(close)
    fvgs = []
    MIN_SIZE = atr_val * 0.3

    for i in range(1, n - 1):
        # Bullish FVG: low[i+1] > high[i-1]
        gap = low[i+1] - high[i-1]
        if gap > MIN_SIZE:
            # Check if mitigated (price came back into gap)
            mitigated = any(low[j] < low[i+1] for j in range(i+2, n))
            mit_pct = 0.0
            if mitigated:
                for j in range(i+2, n):
                    if low[j] < low[i+1]:
                        fill = min(low[j], high[i-1])
                        mit_pct = min(1.0, safe_div(low[i+1] - fill, gap))
                        break
            fvgs.append(PriceZone(
                zone_type=ZoneType.BULLISH_FVG,
                top=low[i+1], bottom=high[i-1],
                bar_index=i, mitigated=mitigated,
                mitigation_pct=mit_pct,
                strength=min(1.0, gap / (atr_val * 2)),
                active=not mitigated, formed_by_close=False,
            ))

        # Bearish FVG: high[i+1] < low[i-1]
        gap = low[i-1] - high[i+1]
        if gap > MIN_SIZE:
            mitigated = any(high[j] > high[i+1] for j in range(i+2, n))
            mit_pct = 0.0
            if mitigated:
                for j in range(i+2, n):
                    if high[j] > high[i+1]:
                        fill = max(high[j], low[i-1])
                        mit_pct = min(1.0, safe_div(fill - high[i+1], gap))
                        break
            fvgs.append(PriceZone(
                zone_type=ZoneType.BEARISH_FVG,
                top=low[i-1], bottom=high[i+1],
                bar_index=i, mitigated=mitigated,
                mitigation_pct=mit_pct,
                strength=min(1.0, gap / (atr_val * 2)),
                active=not mitigated, formed_by_close=False,
            ))

    active_fvgs = [f for f in fvgs if f.active]
    return sorted(active_fvgs, key=lambda f: -f.bar_index)[:max_fvgs]


# ─── Breaker Blocks ───────────────────────────────────────────────────────────

def find_breakers(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    atr_val: float
) -> List[PriceZone]:
    """Breaker: an OB that has been violated; flips polarity."""
    n = len(close)
    breakers = []

    for i in range(2, n - 2):
        body_i = abs(close[i] - open_[i])
        # Bull OB turned bearish breaker: bull candle whose high was broken by price
        if close[i] > open_[i] and body_i > atr_val * 0.3:
            # Was it a valid OB? (preceded a down move)
            if i + 2 < n and close[i+1] < open_[i]:
                # Later price broke ABOVE the high of this candle? → breaker
                broke_above = any(close[j] > high[i] for j in range(i+2, n))
                if broke_above:
                    breakers.append(PriceZone(
                        zone_type=ZoneType.BREAKER_BULL,
                        top=high[i], bottom=open_[i],
                        bar_index=i, mitigated=False, mitigation_pct=0.0,
                        strength=0.7, active=True, formed_by_close=False,
                    ))

        # Bear OB turned bullish breaker
        if close[i] < open_[i] and body_i > atr_val * 0.3:
            if i + 2 < n and close[i+1] > open_[i]:
                broke_below = any(close[j] < low[i] for j in range(i+2, n))
                if broke_below:
                    breakers.append(PriceZone(
                        zone_type=ZoneType.BREAKER_BEAR,
                        top=open_[i], bottom=low[i],
                        bar_index=i, mitigated=False, mitigation_pct=0.0,
                        strength=0.7, active=True, formed_by_close=False,
                    ))

    return sorted(breakers, key=lambda b: -b.bar_index)[:4]


# ─── Liquidity Voids ──────────────────────────────────────────────────────────

def find_liquidity_voids(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float
) -> List[PriceZone]:
    """Areas of thin price coverage = liquidity voids (price magnets)."""
    n = len(close)
    voids = []
    VOID_THRESHOLD = atr_val * 2.0

    for i in range(1, n):
        gap_up = low[i] - high[i-1]
        gap_dn = low[i-1] - high[i]

        if gap_up > VOID_THRESHOLD:
            filled = any(low[j] < low[i] for j in range(i+1, n))
            voids.append(PriceZone(
                zone_type=ZoneType.BULLISH_VOID,
                top=low[i], bottom=high[i-1],
                bar_index=i, mitigated=filled, mitigation_pct=1.0 if filled else 0.0,
                strength=min(1.0, gap_up / (atr_val * 4)),
                active=not filled, formed_by_close=False,
            ))
        elif gap_dn > VOID_THRESHOLD:
            filled = any(high[j] > high[i] for j in range(i+1, n))
            voids.append(PriceZone(
                zone_type=ZoneType.BEARISH_VOID,
                top=low[i-1], bottom=high[i],
                bar_index=i, mitigated=filled, mitigation_pct=1.0 if filled else 0.0,
                strength=min(1.0, gap_dn / (atr_val * 4)),
                active=not filled, formed_by_close=False,
            ))

    return sorted([v for v in voids if v.active], key=lambda v: -v.bar_index)[:6]


# ─── Premium / Discount Arrays ────────────────────────────────────────────────

def calc_premium_discount(swing_high: float, swing_low: float, price: float):
    """Calculate premium/discount/equilibrium zones from swing range."""
    swing_range = swing_high - swing_low
    equilibrium = (swing_high + swing_low) / 2
    premium_top = swing_high
    premium_bottom = equilibrium + swing_range * 0.05  # top 45% = premium
    discount_top = equilibrium - swing_range * 0.05
    discount_bottom = swing_low

    if price > premium_bottom:
        zone = "PREMIUM"
    elif price < discount_top:
        zone = "DISCOUNT"
    else:
        zone = "EQUILIBRIUM"

    return equilibrium, (premium_bottom, premium_top), (discount_bottom, discount_top), zone


# ─── Signal Aggregation ───────────────────────────────────────────────────────

def compute_pa_signal(
    trend: str, price: float,
    current_zone: str,
    last_bos: Optional[StructurePoint],
    last_choch: Optional[StructurePoint],
    order_blocks: List[PriceZone],
    fvgs: List[PriceZone],
    breakers: List[PriceZone],
    atr_val: float,
) -> Tuple[str, float, float]:
    score = 0.0

    # Trend bias
    if trend == "BULLISH":
        score += 0.35
    elif trend == "BEARISH":
        score -= 0.35

    # BOS
    if last_bos:
        if last_bos.type == StructureType.BOS_BULLISH:
            score += 0.25 * last_bos.strength
        else:
            score -= 0.25 * last_bos.strength

    # CHoCH (stronger signal)
    if last_choch:
        if last_choch.type == StructureType.CHOCH_BULLISH:
            score += 0.35 * last_choch.strength
        else:
            score -= 0.35 * last_choch.strength

    # Price in OB
    for ob in order_blocks[:3]:
        if ob.bottom <= price <= ob.top:
            if ob.zone_type == ZoneType.BULLISH_OB:
                score += 0.30 * ob.strength
            else:
                score -= 0.30 * ob.strength

    # Price in FVG
    for fvg in fvgs[:3]:
        if fvg.bottom <= price <= fvg.top:
            if fvg.zone_type == ZoneType.BULLISH_FVG:
                score += 0.20 * fvg.strength
            else:
                score -= 0.20 * fvg.strength

    # Premium/Discount context
    if current_zone == "DISCOUNT" and trend == "BULLISH":
        score += 0.20
    elif current_zone == "PREMIUM" and trend == "BEARISH":
        score -= 0.20
    elif current_zone == "PREMIUM" and trend == "BULLISH":
        score -= 0.10  # caution — extended
    elif current_zone == "DISCOUNT" and trend == "BEARISH":
        score += 0.10  # caution — extended

    score = max(-1.0, min(1.0, score))
    confidence = min(0.95, 0.55 + abs(score) * 0.4)
    vote = "BUY" if score > 0.15 else ("SELL" if score < -0.15 else "NEUTRAL")
    return vote, round(score, 4), round(confidence, 4)


# ─── Master Analyzer ──────────────────────────────────────────────────────────

def analyze_price_action(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    asset: str = "UNKNOWN", timeframe: str = "H1",
) -> PriceActionReport:
    n = len(close)
    atr_val = calc_atr(high, low, close)
    price = float(close[-1])

    # Structure
    trend, last_bos, last_choch, swing_high, swing_low, pivots = analyze_structure(high, low, close, atr_val)

    # Zones
    order_blocks = find_order_blocks(open_, high, low, close, atr_val)
    fvgs = find_fvgs(high, low, close, atr_val)
    breakers = find_breakers(open_, high, low, close, atr_val)
    voids = find_liquidity_voids(high, low, close, atr_val)

    # Premium/Discount
    equilibrium, premium_zone, discount_zone, current_zone = calc_premium_discount(swing_high, swing_low, price)

    # Signal
    vote, score, confidence = compute_pa_signal(
        trend, price, current_zone, last_bos, last_choch, order_blocks, fvgs, breakers, atr_val
    )

    def sp_to_dict(sp: Optional[StructurePoint]) -> Optional[dict]:
        if sp is None:
            return None
        return {"type": sp.type, "bar_index": sp.bar_index, "price": round(sp.price, 5), "strength": round(sp.strength, 4)}

    def zone_to_dict(z: PriceZone) -> dict:
        return {
            "type": z.zone_type, "top": round(z.top, 5), "bottom": round(z.bottom, 5),
            "bar_index": z.bar_index, "mitigated": z.mitigated,
            "mitigation_pct": round(z.mitigation_pct, 3), "strength": round(z.strength, 4),
            "active": z.active,
        }

    return PriceActionReport(
        asset=asset.upper(), timeframe=timeframe.upper(),
        trend=trend, last_bos=last_bos, last_choch=last_choch,
        swing_high=round(swing_high, 5), swing_low=round(swing_low, 5),
        equilibrium=round(equilibrium, 5),
        premium_zone=(round(premium_zone[0], 5), round(premium_zone[1], 5)),
        discount_zone=(round(discount_zone[0], 5), round(discount_zone[1], 5)),
        current_zone=current_zone,
        order_blocks=order_blocks, fvgs=fvgs,
        breakers=breakers, voids=voids,
        vote=vote, score=score, confidence=confidence,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


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


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "price-action-service"}


@app.post("/analyze")
async def analyze(req: PAScanRequest):
    open_ = np.array(req.ohlcv.open)
    high  = np.array(req.ohlcv.high)
    low   = np.array(req.ohlcv.low)
    close = np.array(req.ohlcv.close)

    if len(close) < 20:
        raise HTTPException(400, "Need at least 20 bars")

    cache_key = f"pa:{req.asset}:{req.timeframe}:{hash(tuple(close[-5:]))}"
    redis = await get_redis()
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

    report = analyze_price_action(open_, high, low, close, req.asset, req.timeframe)

    def zone_list(zones):
        return [
            {"type": z.zone_type, "top": round(z.top, 5), "bottom": round(z.bottom, 5),
             "bar_index": z.bar_index, "strength": round(z.strength, 4),
             "mitigated": z.mitigated, "mitigation_pct": round(z.mitigation_pct, 3)}
            for z in zones
        ]

    def sp_dict(sp):
        if sp is None: return None
        return {"type": sp.type, "bar_index": sp.bar_index, "price": round(sp.price, 5), "strength": round(sp.strength, 4)}

    result = {
        "asset": report.asset, "timeframe": report.timeframe,
        "trend": report.trend,
        "last_bos": sp_dict(report.last_bos),
        "last_choch": sp_dict(report.last_choch),
        "swing_high": report.swing_high, "swing_low": report.swing_low,
        "equilibrium": report.equilibrium,
        "premium_zone": list(report.premium_zone),
        "discount_zone": list(report.discount_zone),
        "current_zone": report.current_zone,
        "order_blocks": zone_list(report.order_blocks),
        "fvgs": zone_list(report.fvgs),
        "breakers": zone_list(report.breakers),
        "voids": zone_list(report.voids),
        "signal": {"vote": report.vote, "score": report.score, "confidence": report.confidence},
        "generated_at": report.generated_at,
    }

    if redis:
        await redis.setex(cache_key, 60, json.dumps(result))

    return result


@app.post("/analyze/structure")
async def analyze_structure_only(req: PAScanRequest):
    high  = np.array(req.ohlcv.high)
    low   = np.array(req.ohlcv.low)
    close = np.array(req.ohlcv.close)
    atr_val = calc_atr(high, low, close)
    trend, last_bos, last_choch, sh, sl, pivots = analyze_structure(high, low, close, atr_val)
    return {
        "trend": trend,
        "swing_high": round(sh, 5), "swing_low": round(sl, 5),
        "last_bos": {"type": last_bos.type, "price": round(last_bos.price, 5)} if last_bos else None,
        "last_choch": {"type": last_choch.type, "price": round(last_choch.price, 5)} if last_choch else None,
        "pivot_count": len(pivots),
    }


@app.post("/analyze/zones")
async def analyze_zones_only(req: PAScanRequest):
    open_ = np.array(req.ohlcv.open)
    high  = np.array(req.ohlcv.high)
    low   = np.array(req.ohlcv.low)
    close = np.array(req.ohlcv.close)
    atr_val = calc_atr(high, low, close)
    obs = find_order_blocks(open_, high, low, close, atr_val)
    fvgs = find_fvgs(high, low, close, atr_val)
    breakers = find_breakers(open_, high, low, close, atr_val)
    voids = find_liquidity_voids(high, low, close, atr_val)

    def zl(zones): return [{"type": z.zone_type, "top": round(z.top, 5), "bottom": round(z.bottom, 5), "strength": round(z.strength, 4)} for z in zones]
    return {"order_blocks": zl(obs), "fvgs": zl(fvgs), "breakers": zl(breakers), "voids": zl(voids)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("price_action:app", host="0.0.0.0", port=8010, reload=False)
