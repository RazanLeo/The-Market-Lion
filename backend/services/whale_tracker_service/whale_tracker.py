"""Whale Tracker Service — The Market Lion.
Detects: large-volume anomalies, dark pool prints, cumulative delta divergence,
stop hunts, institutional order flow, on-chain proxy signals (BTC/ETH).
FastAPI + Redis. Publishes alerts to Kafka.
"""
import asyncio
import logging
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

import numpy as np
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import redis.asyncio as aioredis
from aiokafka import AIOKafkaProducer

logger = logging.getLogger("whale-tracker")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Whale Tracker Service", version="1.0.0")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/6")
KAFKA_URL = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
GLASSNODE_KEY = os.getenv("GLASSNODE_API_KEY", "")
ALTERNATIVE_ME_URL = "https://api.alternative.me/fng/"
COINGECKO_URL = "https://api.coingecko.com/api/v3"


# ─── Models ───────────────────────────────────────────────────────────────────

class WhaleAlertLevel(str, Enum):
    CRITICAL = "CRITICAL"   # >5x avg volume
    HIGH     = "HIGH"       # >3x avg volume
    MEDIUM   = "MEDIUM"     # >2x avg volume
    LOW      = "LOW"        # >1.5x avg volume


class FlowDirection(str, Enum):
    BULLISH  = "BULLISH"
    BEARISH  = "BEARISH"
    NEUTRAL  = "NEUTRAL"
    MIXED    = "MIXED"


@dataclass
class WhaleBar:
    bar_index: int
    volume: float
    volume_ratio: float          # relative to avg
    close: float
    direction: FlowDirection     # was the bar bullish or bearish?
    alert_level: WhaleAlertLevel
    estimated_usd_value: float


@dataclass
class DarkPoolLevel:
    price: float
    estimated_volume: float
    volume_ratio: float
    zone_top: float
    zone_bottom: float
    is_support: bool             # True = support, False = resistance
    strength: float


@dataclass
class CumulativeDeltaSignal:
    delta_trend: str             # BULLISH / BEARISH / DIVERGING
    price_trend: str
    divergence: bool             # price and delta moving opposite
    delta_20: float              # delta over last 20 bars
    buy_pressure: float          # 0-1
    sell_pressure: float         # 0-1
    absorption: bool             # high vol + small price move


@dataclass
class StopHuntSignal:
    detected: bool
    direction: FlowDirection     # BULLISH = hunted lows (expect up), BEARISH = hunted highs
    hunt_level: float
    recovered_above: bool
    bars_since_hunt: int
    strength: float


@dataclass
class WhaleReport:
    asset: str
    timeframe: str
    # Whale activity
    whale_bars: List[WhaleBar]
    total_whale_bars: int
    dominant_flow: FlowDirection
    flow_score: float              # -1 to +1
    # Dark pool
    dark_pool_levels: List[DarkPoolLevel]
    nearest_dp_support: Optional[float]
    nearest_dp_resistance: Optional[float]
    # Delta
    cumulative_delta: CumulativeDeltaSignal
    # Stop hunt
    stop_hunt: StopHuntSignal
    # On-chain (crypto only)
    fear_greed_index: Optional[int]
    fear_greed_label: Optional[str]
    # Signal
    vote: str
    score: float
    confidence: float
    generated_at: str


class OHLCVInput(BaseModel):
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: Optional[List[float]] = None


class WhaleTrackRequest(BaseModel):
    asset: str
    timeframe: str
    ohlcv: OHLCVInput
    include_onchain: bool = False


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


def estimate_price_per_unit(asset: str, close: float) -> float:
    """Estimate USD value per volume unit for sizing."""
    if "XAU" in asset:
        return close * 100       # 1 lot gold = 100 oz
    elif "BTC" in asset:
        return close             # 1 BTC
    elif "ETH" in asset:
        return close
    elif "OIL" in asset or "XBR" in asset:
        return close * 1000      # barrels
    else:
        return close * 100000    # forex: standard lot = 100k units


# ─── Whale Bar Detection ──────────────────────────────────────────────────────

def detect_whale_bars(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray,
    close: np.ndarray, volume: np.ndarray, asset: str,
    lookback: int = 50, threshold: float = 1.5,
) -> List[WhaleBar]:
    n = len(close)
    if n < lookback:
        return []

    avg_vol = float(np.mean(volume[-lookback:]))
    whale_bars = []

    for i in range(max(0, n - lookback), n):
        ratio = safe_div(volume[i], avg_vol)
        if ratio < threshold:
            continue

        if ratio >= 5.0:
            level = WhaleAlertLevel.CRITICAL
        elif ratio >= 3.0:
            level = WhaleAlertLevel.HIGH
        elif ratio >= 2.0:
            level = WhaleAlertLevel.MEDIUM
        else:
            level = WhaleAlertLevel.LOW

        direction = FlowDirection.BULLISH if close[i] >= open_[i] else FlowDirection.BEARISH
        price_per_unit = estimate_price_per_unit(asset, close[i])

        whale_bars.append(WhaleBar(
            bar_index=i,
            volume=float(volume[i]),
            volume_ratio=round(ratio, 2),
            close=float(close[i]),
            direction=direction,
            alert_level=level,
            estimated_usd_value=round(volume[i] * price_per_unit, 0),
        ))

    return sorted(whale_bars, key=lambda w: -w.volume_ratio)


def dominant_flow(whale_bars: List[WhaleBar]) -> Tuple[FlowDirection, float]:
    if not whale_bars:
        return FlowDirection.NEUTRAL, 0.0
    bull_vol = sum(w.volume * w.volume_ratio for w in whale_bars if w.direction == FlowDirection.BULLISH)
    bear_vol = sum(w.volume * w.volume_ratio for w in whale_bars if w.direction == FlowDirection.BEARISH)
    total = bull_vol + bear_vol + 1e-10
    score = (bull_vol - bear_vol) / total
    if score > 0.2:
        return FlowDirection.BULLISH, round(score, 4)
    elif score < -0.2:
        return FlowDirection.BEARISH, round(score, 4)
    return FlowDirection.MIXED, round(score, 4)


# ─── Dark Pool Level Detection ────────────────────────────────────────────────

def detect_dark_pool_levels(
    close: np.ndarray, volume: np.ndarray,
    lookback: int = 100, n_levels: int = 5,
) -> List[DarkPoolLevel]:
    """High-volume price clusters = dark pool accumulation/distribution."""
    n = len(close)
    lb = min(n, lookback)
    prices = close[-lb:]
    vols = volume[-lb:]
    avg_vol = float(np.mean(vols))

    if avg_vol == 0:
        return []

    # Build price histogram weighted by volume
    price_min = float(np.min(prices))
    price_max = float(np.max(prices))
    if price_max == price_min:
        return []

    n_buckets = 20
    bucket_size = (price_max - price_min) / n_buckets
    hist = np.zeros(n_buckets)

    for i in range(lb):
        b = int((prices[i] - price_min) / bucket_size)
        b = max(0, min(n_buckets - 1, b))
        hist[b] += vols[i]

    avg_bucket_vol = np.mean(hist)
    current_price = float(close[-1])
    levels = []

    for b in range(n_buckets):
        if hist[b] > avg_bucket_vol * 2.0:  # dark pool threshold
            level_price = price_min + (b + 0.5) * bucket_size
            zone_bottom = price_min + b * bucket_size
            zone_top = price_min + (b + 1) * bucket_size
            ratio = safe_div(hist[b], avg_bucket_vol)
            is_support = level_price < current_price
            strength = min(1.0, ratio / 5.0)
            levels.append(DarkPoolLevel(
                price=round(level_price, 5),
                estimated_volume=round(float(hist[b]), 2),
                volume_ratio=round(ratio, 2),
                zone_top=round(zone_top, 5),
                zone_bottom=round(zone_bottom, 5),
                is_support=is_support,
                strength=round(strength, 4),
            ))

    return sorted(levels, key=lambda l: -l.volume_ratio)[:n_levels]


# ─── Cumulative Delta ─────────────────────────────────────────────────────────

def calc_cumulative_delta(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray,
    close: np.ndarray, volume: np.ndarray,
) -> CumulativeDeltaSignal:
    n = len(close)
    if n < 5:
        return CumulativeDeltaSignal("NEUTRAL", "NEUTRAL", False, 0.0, 0.5, 0.5, False)

    # Estimate per-bar delta: bullish bar = +vol, bearish = -vol, proportional to close position
    bar_positions = np.array([
        safe_div(close[i] - low[i], high[i] - low[i] + 1e-10)
        for i in range(n)
    ])
    ask_vol = volume * bar_positions
    bid_vol = volume * (1 - bar_positions)
    delta = ask_vol - bid_vol
    cum_delta = np.cumsum(delta)

    lookback = min(20, n)
    delta_20 = float(cum_delta[-1] - cum_delta[-lookback])
    price_20 = float(close[-1] - close[-lookback])

    # Trends
    delta_trend = "BULLISH" if delta_20 > 0 else "BEARISH"
    price_trend = "BULLISH" if price_20 > 0 else "BEARISH"

    # Divergence: delta going opposite direction to price
    divergence = (delta_20 > 0) != (price_20 > 0) and abs(delta_20) > float(np.std(delta[-lookback:]) * 2)

    # Buy/sell pressure
    buy_pressure = float(np.mean(bar_positions[-10:]))
    sell_pressure = 1.0 - buy_pressure

    # Absorption: high volume + small price move
    vol_ratio = safe_div(float(np.mean(volume[-5:])), float(np.mean(volume[-20:])))
    atr_proxy = float(np.mean(np.abs(np.diff(close[-20:]))))
    recent_move = abs(price_20 / lookback)
    absorption = vol_ratio > 1.5 and recent_move < atr_proxy * 0.3

    return CumulativeDeltaSignal(
        delta_trend=delta_trend,
        price_trend=price_trend,
        divergence=divergence,
        delta_20=round(delta_20, 2),
        buy_pressure=round(buy_pressure, 4),
        sell_pressure=round(sell_pressure, 4),
        absorption=absorption,
    )


# ─── Stop Hunt Detection ──────────────────────────────────────────────────────

def detect_stop_hunt(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_val: float
) -> StopHuntSignal:
    n = len(close)
    lookback = min(n, 30)

    # Find recent equal highs/lows (stop clusters)
    tolerance = atr_val * 0.15
    highs_lb = high[-lookback:]
    lows_lb = low[-lookback:]

    max_high = float(np.max(highs_lb[:-3]))
    min_low = float(np.min(lows_lb[:-3]))

    # Bullish stop hunt: price swept below min_low then recovered
    recent_low = float(np.min(low[-5:]))
    recent_close = float(close[-1])

    swept_low = recent_low < min_low and recent_close > min_low
    swept_high = float(np.max(high[-5:])) > max_high and recent_close < max_high

    if swept_low:
        wick_depth = min_low - recent_low
        strength = min(1.0, safe_div(wick_depth, atr_val))
        # Find how many bars ago
        bars_since = 0
        for i in range(n-1, max(n-6, 0), -1):
            if low[i] <= min_low:
                bars_since = n - 1 - i
                break
        return StopHuntSignal(
            detected=True, direction=FlowDirection.BULLISH,
            hunt_level=round(min_low, 5), recovered_above=True,
            bars_since_hunt=bars_since, strength=round(strength, 4),
        )
    elif swept_high:
        wick_height = float(np.max(high[-5:])) - max_high
        strength = min(1.0, safe_div(wick_height, atr_val))
        bars_since = 0
        for i in range(n-1, max(n-6, 0), -1):
            if high[i] >= max_high:
                bars_since = n - 1 - i
                break
        return StopHuntSignal(
            detected=True, direction=FlowDirection.BEARISH,
            hunt_level=round(max_high, 5), recovered_above=False,
            bars_since_hunt=bars_since, strength=round(strength, 4),
        )

    return StopHuntSignal(
        detected=False, direction=FlowDirection.NEUTRAL,
        hunt_level=0.0, recovered_above=False, bars_since_hunt=0, strength=0.0,
    )


# ─── On-Chain (Fear & Greed) ──────────────────────────────────────────────────

async def fetch_fear_greed() -> Tuple[Optional[int], Optional[str]]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ALTERNATIVE_ME_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    entry = data.get("data", [{}])[0]
                    return int(entry.get("value", 50)), entry.get("value_classification", "Neutral")
    except Exception as e:
        logger.warning(f"Fear & greed fetch error: {e}")
    return None, None


async def fetch_coingecko_dominance() -> Dict[str, float]:
    """Fetch BTC dominance as market sentiment proxy."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{COINGECKO_URL}/global"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    market = data.get("data", {}).get("market_cap_percentage", {})
                    return {"btc": market.get("btc", 50), "eth": market.get("eth", 20)}
    except Exception:
        pass
    return {"btc": 50.0, "eth": 20.0}


# ─── Signal Aggregation ───────────────────────────────────────────────────────

def compute_whale_signal(
    flow_score: float,
    delta_signal: CumulativeDeltaSignal,
    stop_hunt: StopHuntSignal,
    dark_pool_levels: List[DarkPoolLevel],
    current_price: float,
    fear_greed: Optional[int],
) -> Tuple[str, float, float]:
    score = 0.0

    # Whale flow
    score += flow_score * 0.35

    # Cumulative delta
    if delta_signal.delta_trend == "BULLISH" and not delta_signal.divergence:
        score += 0.20
    elif delta_signal.delta_trend == "BEARISH" and not delta_signal.divergence:
        score -= 0.20

    # Divergence (contra-signal)
    if delta_signal.divergence:
        if delta_signal.price_trend == "BULLISH":
            score -= 0.15  # price up but delta down = hidden selling
        else:
            score += 0.15  # price down but delta up = hidden buying

    # Stop hunt
    if stop_hunt.detected:
        if stop_hunt.direction == FlowDirection.BULLISH:
            score += 0.25 * stop_hunt.strength
        else:
            score -= 0.25 * stop_hunt.strength

    # Dark pool nearest level
    if dark_pool_levels:
        supports = [l for l in dark_pool_levels if l.is_support]
        resists  = [l for l in dark_pool_levels if not l.is_support]
        if supports:
            nearest_sup = max(supports, key=lambda l: l.price)
            dist_sup = safe_div(current_price - nearest_sup.price, current_price)
            if dist_sup < 0.005:
                score += 0.20 * nearest_sup.strength
        if resists:
            nearest_res = min(resists, key=lambda l: l.price)
            dist_res = safe_div(nearest_res.price - current_price, current_price)
            if dist_res < 0.005:
                score -= 0.20 * nearest_res.strength

    # Fear & Greed (crypto only)
    if fear_greed is not None:
        fg_score = (fear_greed - 50) / 100.0
        score += fg_score * 0.10

    score = max(-1.0, min(1.0, score))
    confidence = 0.55 + abs(score) * 0.35
    vote = "BUY" if score > 0.15 else ("SELL" if score < -0.15 else "NEUTRAL")
    return vote, round(score, 4), round(min(0.95, confidence), 4)


# ─── Master Analyzer ──────────────────────────────────────────────────────────

async def analyze_whale_activity(req: WhaleTrackRequest) -> WhaleReport:
    open_  = np.array(req.ohlcv.open)
    high   = np.array(req.ohlcv.high)
    low    = np.array(req.ohlcv.low)
    close  = np.array(req.ohlcv.close)
    volume = np.array(req.ohlcv.volume) if req.ohlcv.volume else np.ones(len(close))

    n = len(close)
    atr_val = calc_atr(high, low, close)

    # Whale bar detection
    whale_bars = detect_whale_bars(open_, high, low, close, volume, req.asset)
    flow_dir, flow_score = dominant_flow(whale_bars)

    # Dark pool levels
    dp_levels = detect_dark_pool_levels(close, volume)
    price = float(close[-1])
    dp_supports = [l for l in dp_levels if l.is_support]
    dp_resists  = [l for l in dp_levels if not l.is_support]
    nearest_sup = round(max((l.price for l in dp_supports), default=price * 0.99), 5)
    nearest_res = round(min((l.price for l in dp_resists), default=price * 1.01), 5)

    # Cumulative delta
    cum_delta = calc_cumulative_delta(open_, high, low, close, volume)

    # Stop hunt
    stop_hunt = detect_stop_hunt(high, low, close, atr_val)

    # On-chain data (async, optional)
    fg_index, fg_label = None, None
    if req.include_onchain and any(c in req.asset.upper() for c in ["BTC", "ETH", "SOL"]):
        fg_index, fg_label = await fetch_fear_greed()

    # Signal
    vote, score, confidence = compute_whale_signal(
        flow_score, cum_delta, stop_hunt, dp_levels, price, fg_index
    )

    return WhaleReport(
        asset=req.asset.upper(), timeframe=req.timeframe.upper(),
        whale_bars=whale_bars[-10:],
        total_whale_bars=len(whale_bars),
        dominant_flow=flow_dir,
        flow_score=flow_score,
        dark_pool_levels=dp_levels,
        nearest_dp_support=nearest_sup,
        nearest_dp_resistance=nearest_res,
        cumulative_delta=cum_delta,
        stop_hunt=stop_hunt,
        fear_greed_index=fg_index,
        fear_greed_label=fg_label,
        vote=vote, score=score, confidence=confidence,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ─── Redis + Kafka ────────────────────────────────────────────────────────────

_redis: Optional[aioredis.Redis] = None
_kafka: Optional[AIOKafkaProducer] = None


async def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        except Exception:
            pass
    return _redis


async def get_kafka():
    global _kafka
    if _kafka is None:
        try:
            _kafka = AIOKafkaProducer(bootstrap_servers=KAFKA_URL)
            await _kafka.start()
        except Exception:
            _kafka = None
    return _kafka


async def publish_whale_alert(report: WhaleReport):
    producer = await get_kafka()
    if not producer:
        return
    critical_bars = [w for w in report.whale_bars if w.alert_level == WhaleAlertLevel.CRITICAL]
    if not critical_bars or abs(report.score) < 0.4:
        return
    payload = {
        "type": "whale_alert",
        "asset": report.asset, "timeframe": report.timeframe,
        "vote": report.vote, "score": report.score,
        "dominant_flow": report.dominant_flow,
        "critical_bars": len(critical_bars),
        "stop_hunt": report.stop_hunt.detected,
        "delta_divergence": report.cumulative_delta.divergence,
        "generated_at": report.generated_at,
    }
    try:
        await producer.send_and_wait("whale_alerts", json.dumps(payload, default=str).encode())
    except Exception as e:
        logger.warning(f"Kafka publish error: {e}")


# ─── Serialization helpers ────────────────────────────────────────────────────

def wb_to_dict(w: WhaleBar) -> dict:
    return {
        "bar_index": w.bar_index, "volume": round(w.volume, 2),
        "volume_ratio": w.volume_ratio, "close": round(w.close, 5),
        "direction": w.direction, "alert_level": w.alert_level,
        "estimated_usd_value": w.estimated_usd_value,
    }


def dp_to_dict(d: DarkPoolLevel) -> dict:
    return {
        "price": d.price, "volume_ratio": d.volume_ratio,
        "zone_top": d.zone_top, "zone_bottom": d.zone_bottom,
        "is_support": d.is_support, "strength": d.strength,
    }


def cd_to_dict(c: CumulativeDeltaSignal) -> dict:
    return {
        "delta_trend": c.delta_trend, "price_trend": c.price_trend,
        "divergence": c.divergence, "delta_20": c.delta_20,
        "buy_pressure": c.buy_pressure, "sell_pressure": c.sell_pressure,
        "absorption": c.absorption,
    }


def sh_to_dict(s: StopHuntSignal) -> dict:
    return {
        "detected": s.detected, "direction": s.direction,
        "hunt_level": round(s.hunt_level, 5), "recovered_above": s.recovered_above,
        "bars_since_hunt": s.bars_since_hunt, "strength": s.strength,
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("Whale Tracker Service started")


@app.on_event("shutdown")
async def shutdown():
    producer = await get_kafka()
    if producer:
        await producer.stop()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "whale-tracker"}


@app.post("/analyze")
async def analyze(req: WhaleTrackRequest, background_tasks: BackgroundTasks):
    if len(req.ohlcv.close) < 20:
        raise HTTPException(400, "Need at least 20 bars")

    redis = await get_redis()
    cache_key = f"whale:{req.asset}:{req.timeframe}"
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

    report = await analyze_whale_activity(req)

    result = {
        "asset": report.asset, "timeframe": report.timeframe,
        "whale_activity": {
            "total_whale_bars": report.total_whale_bars,
            "dominant_flow": report.dominant_flow,
            "flow_score": report.flow_score,
            "top_bars": [wb_to_dict(w) for w in report.whale_bars[:5]],
        },
        "dark_pool": {
            "levels": [dp_to_dict(d) for d in report.dark_pool_levels],
            "nearest_support": report.nearest_dp_support,
            "nearest_resistance": report.nearest_dp_resistance,
        },
        "cumulative_delta": cd_to_dict(report.cumulative_delta),
        "stop_hunt": sh_to_dict(report.stop_hunt),
        "onchain": {
            "fear_greed_index": report.fear_greed_index,
            "fear_greed_label": report.fear_greed_label,
        } if report.fear_greed_index is not None else None,
        "signal": {"vote": report.vote, "score": report.score, "confidence": report.confidence},
        "generated_at": report.generated_at,
    }

    if redis:
        await redis.setex(cache_key, 60, json.dumps(result))

    background_tasks.add_task(publish_whale_alert, report)
    return result


@app.post("/analyze/dark-pool")
async def analyze_dark_pool_only(req: WhaleTrackRequest):
    close  = np.array(req.ohlcv.close)
    volume = np.array(req.ohlcv.volume) if req.ohlcv.volume else np.ones(len(close))
    levels = detect_dark_pool_levels(close, volume)
    return {"asset": req.asset, "levels": [dp_to_dict(d) for d in levels]}


@app.post("/analyze/delta")
async def analyze_delta_only(req: WhaleTrackRequest):
    open_  = np.array(req.ohlcv.open)
    high   = np.array(req.ohlcv.high)
    low    = np.array(req.ohlcv.low)
    close  = np.array(req.ohlcv.close)
    volume = np.array(req.ohlcv.volume) if req.ohlcv.volume else np.ones(len(close))
    signal = calc_cumulative_delta(open_, high, low, close, volume)
    return cd_to_dict(signal)


@app.post("/analyze/stop-hunt")
async def analyze_stop_hunt_only(req: WhaleTrackRequest):
    high  = np.array(req.ohlcv.high)
    low   = np.array(req.ohlcv.low)
    close = np.array(req.ohlcv.close)
    atr_v = calc_atr(high, low, close)
    signal = detect_stop_hunt(high, low, close, atr_v)
    return sh_to_dict(signal)


@app.get("/fear-greed")
async def fear_greed_endpoint():
    index, label = await fetch_fear_greed()
    if index is None:
        raise HTTPException(503, "Fear & Greed data unavailable")
    return {"index": index, "label": label, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/dominance")
async def dominance_endpoint():
    data = await fetch_coingecko_dominance()
    return {"data": data, "timestamp": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("whale_tracker:app", host="0.0.0.0", port=8012, reload=False)
