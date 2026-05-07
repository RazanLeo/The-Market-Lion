"""Full Bookmap engine — heatmap state, L2 order book, iceberg, absorption, sweep detection.

Inputs (from broker streams when available, else demo synthesizer):
  - L2 snapshots: dict[price -> size] for bid and ask sides.
  - Trade tape: each trade {ts, price, size, side}.
"""
from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Deque

import numpy as np
import redis.asyncio as aioredis

from ..core.config import settings
from ..core.logging import get_logger

log = get_logger("bookmap")


@dataclass
class HeatmapCell:
    price: float
    size: float
    side: str  # "bid" | "ask"
    intensity: float  # log-normalized 0..100
    refilled_count: int = 0


@dataclass
class BookmapState:
    symbol: str
    bids: dict[float, float] = field(default_factory=dict)
    asks: dict[float, float] = field(default_factory=dict)
    tape: Deque[dict] = field(default_factory=lambda: deque(maxlen=2000))
    cvd: float = 0.0
    iceberg_zones: list[dict] = field(default_factory=list)
    absorption_zones: list[dict] = field(default_factory=list)
    sweeps: list[dict] = field(default_factory=list)
    last_refresh: float = 0.0
    refill_tracker: dict[float, int] = field(default_factory=lambda: defaultdict(int))


class BookmapEngine:
    def __init__(self, symbol: str):
        self.state = BookmapState(symbol=symbol)
        self._redis: aioredis.Redis | None = None

    async def connect(self):
        self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    def update_book(self, bids: dict[float, float], asks: dict[float, float]) -> None:
        # Detect iceberg: a price level whose size keeps refilling
        for p in list(self.state.bids):
            if p in bids and bids[p] >= self.state.bids[p] * 0.95:
                self.state.refill_tracker[p] += 1
            else:
                self.state.refill_tracker.pop(p, None)
        for p in list(self.state.asks):
            if p in asks and asks[p] >= self.state.asks[p] * 0.95:
                self.state.refill_tracker[p] += 1
            else:
                self.state.refill_tracker.pop(p, None)
        self.state.bids = dict(bids)
        self.state.asks = dict(asks)
        self.state.iceberg_zones = [
            {"price": p, "refills": n} for p, n in self.state.refill_tracker.items() if n >= 3
        ]
        self.state.last_refresh = time.time()

    def add_trade(self, ts: float, price: float, size: float, side: str) -> None:
        sgn = 1 if side == "buy" else -1
        self.state.cvd += sgn * size
        self.state.tape.append({"ts": ts, "p": price, "s": size, "side": side})
        self._detect_absorption()
        self._detect_sweep()

    def _detect_absorption(self) -> None:
        """Large $ traded but price doesn't move ⇒ strong opposite side absorbing."""
        if len(self.state.tape) < 50: return
        win = list(self.state.tape)[-50:]
        prices = [t["p"] for t in win]
        if max(prices) - min(prices) < 0.0001: return  # avoid div by zero on flat
        sizes = [t["s"] for t in win]
        median_size = np.median(sizes)
        for t in win[-5:]:
            if t["s"] > median_size * 5 and abs(t["p"] - prices[-1]) < (max(prices) - min(prices)) * 0.05:
                self.state.absorption_zones.append({
                    "ts": t["ts"], "price": t["p"], "size": t["s"], "side_absorbing": "ask" if t["side"] == "buy" else "bid",
                })

    def _detect_sweep(self) -> None:
        """Quick liquidity sweep: price spikes, then snaps back."""
        if len(self.state.tape) < 10: return
        win = list(self.state.tape)[-10:]
        prices = [t["p"] for t in win]
        rng = max(prices) - min(prices)
        if rng < 0.0001: return
        # if price made a new high but pulled back > 60% of range
        idx_high = int(np.argmax(prices))
        if idx_high < len(prices) - 1 and (max(prices) - prices[-1]) / rng > 0.6:
            self.state.sweeps.append({"type": "BSL_sweep", "high": max(prices), "back_to": prices[-1]})
        idx_low = int(np.argmin(prices))
        if idx_low < len(prices) - 1 and (prices[-1] - min(prices)) / rng > 0.6:
            self.state.sweeps.append({"type": "SSL_sweep", "low": min(prices), "back_to": prices[-1]})

    def heatmap_payload(self) -> dict[str, Any]:
        # Log-normalize sizes 0..100
        all_sizes = list(self.state.bids.values()) + list(self.state.asks.values())
        if not all_sizes: return {"bids": [], "asks": [], "icebergs": [], "absorption": [], "sweeps": [], "cvd": self.state.cvd}
        max_s = max(all_sizes); ln_max = np.log1p(max_s)
        def cells(side: dict[float, float], lbl: str):
            return [{
                "p": p, "s": s, "side": lbl,
                "intensity": float(np.log1p(s) / ln_max * 100) if ln_max > 0 else 0,
            } for p, s in sorted(side.items())]
        return {
            "bids": cells(self.state.bids, "bid"),
            "asks": cells(self.state.asks, "ask"),
            "icebergs": self.state.iceberg_zones,
            "absorption": self.state.absorption_zones[-20:],
            "sweeps": self.state.sweeps[-20:],
            "cvd": self.state.cvd,
            "ts": self.state.last_refresh,
        }

    async def publish(self):
        if not self._redis: return
        await self._redis.publish(f"bookmap:{self.state.symbol}", json.dumps(self.heatmap_payload()))


# Demo synthesizer for development without L2 stream
async def demo_feed(symbol: str = "XAUUSD") -> AsyncIterator[dict]:
    base = 2300.0
    while True:
        spread = 0.5
        bids = {round(base - spread - i*0.5, 2): float(np.random.randint(50, 500)) for i in range(20)}
        asks = {round(base + spread + i*0.5, 2): float(np.random.randint(50, 500)) for i in range(20)}
        yield {"type": "book", "bids": bids, "asks": asks}
        for _ in range(5):
            side = "buy" if np.random.rand() > 0.5 else "sell"
            yield {"type": "trade", "price": base + (np.random.rand() - 0.5) * 2, "size": float(np.random.randint(1, 200)), "side": side, "ts": time.time()}
        base += (np.random.rand() - 0.5) * 1.5
        await asyncio.sleep(0.25)


async def run_demo(symbol: str = "XAUUSD") -> None:
    eng = BookmapEngine(symbol); await eng.connect()
    async for evt in demo_feed(symbol):
        if evt["type"] == "book":
            eng.update_book(evt["bids"], evt["asks"])
        else:
            eng.add_trade(evt["ts"], evt["price"], evt["size"], evt["side"])
        await eng.publish()
