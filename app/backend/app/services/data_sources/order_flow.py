"""Order Flow / Bookmap public sources — Binance public WS for crypto + yfinance volume profile for FX/commodities.

Binance offers free public WebSocket streams for depth (L2 order book) and aggregate
trades. For non-crypto symbols (gold, oil, FX) we reconstruct order flow from yfinance
intraday OHLCV using the candle-position-weighted volume estimator.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterator

import httpx
import pandas as pd

from ...core.logging import get_logger

log = get_logger("order_flow")

# Public Binance REST endpoints — depth + recent aggregate trades (no API key)
BINANCE_DEPTH = "https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}"
BINANCE_AGG_TRADES = "https://api.binance.com/api/v3/aggTrades?symbol={symbol}&limit=500"

# Symbol mapping: platform → Binance pair (only crypto)
SYMBOL_TO_BINANCE = {
    "BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT",
    "SOLUSD": "SOLUSDT", "BNBUSD": "BNBUSDT",
}


def binance_depth(symbol: str, limit: int = 50) -> dict[str, Any]:
    """Pull current order-book depth for a crypto pair from Binance.

    Returns {bids: [[price, qty], ...], asks: [[price, qty], ...], last_update_id}.
    Only valid for crypto symbols; returns empty dict for FX/commodities.
    """
    binance_sym = SYMBOL_TO_BINANCE.get(symbol.upper())
    if not binance_sym:
        return {}
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(BINANCE_DEPTH.format(symbol=binance_sym, limit=limit))
            if r.status_code != 200:
                return {}
            data = r.json()
        return {
            "symbol": symbol.upper(),
            "ts": datetime.now(timezone.utc).isoformat(),
            "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
            "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
            "last_update_id": data.get("lastUpdateId"),
            "source": "binance",
        }
    except Exception as e:  # pragma: no cover
        log.warning("binance_depth_failed", symbol=symbol, err=str(e))
        return {}


def binance_agg_trades(symbol: str) -> list[dict[str, Any]]:
    """Recent 500 aggregate trades from Binance (price, qty, side, ts)."""
    binance_sym = SYMBOL_TO_BINANCE.get(symbol.upper())
    if not binance_sym:
        return []
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(BINANCE_AGG_TRADES.format(symbol=binance_sym))
            if r.status_code != 200:
                return []
            data = r.json()
        out = []
        for t in data:
            out.append({
                "ts": datetime.fromtimestamp(t["T"] / 1000, tz=timezone.utc).isoformat(),
                "price": float(t["p"]), "qty": float(t["q"]),
                "is_buyer_maker": bool(t["m"]),
                "side": "sell" if t["m"] else "buy",
            })
        return out
    except Exception as e:  # pragma: no cover
        log.warning("binance_trades_failed", symbol=symbol, err=str(e))
        return []


def reconstruct_order_flow(df: pd.DataFrame) -> dict[str, Any]:
    """Estimate buy/sell volume from OHLCV candle position (for non-crypto symbols).

    Uses the standard tick-rule proxy:
        buy_vol  = volume × (close - low) / (high - low)
        sell_vol = volume × (high - close) / (high - low)
    Then computes:
        delta = buy_vol - sell_vol
        cvd   = cumulative delta over the window
        absorption_bars = bars with high vol & narrow range (institutional absorption)
        sweep_events    = wicks beyond prior swing extremes
    """
    if df.empty or "v" not in df.columns:
        return {}

    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    pos = (df["c"] - df["l"]) / rng
    buy_vol = df["v"] * pos
    sell_vol = df["v"] * (1 - pos)
    delta = buy_vol - sell_vol
    cvd = delta.cumsum()

    # ATR for absorption detection
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    vol_avg = df["v"].rolling(20).mean()

    absorption = ((rng < atr * 0.4) & (df["v"] > vol_avg * 1.8)).sum()
    sweeps_up = ((df["h"] > df["h"].rolling(20).max().shift(1)) & (df["c"] < df["h"])).sum()
    sweeps_dn = ((df["l"] < df["l"].rolling(20).min().shift(1)) & (df["c"] > df["l"])).sum()

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "buy_volume":  round(float(buy_vol.sum()), 2),
        "sell_volume": round(float(sell_vol.sum()), 2),
        "delta": round(float(delta.sum()), 2),
        "cvd_last": round(float(cvd.iloc[-1]) if len(cvd) else 0, 2),
        "absorption_bars": int(absorption),
        "sweeps_up": int(sweeps_up),
        "sweeps_dn": int(sweeps_dn),
        "imbalance_pct": round(float((buy_vol.sum() - sell_vol.sum()) /
                                      (buy_vol.sum() + sell_vol.sum() + 1e-9) * 100), 2),
        "source": "ohlcv_reconstruction",
    }


def get_order_flow(symbol: str, df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Unified entry-point: Binance for crypto, OHLCV reconstruction for everything else."""
    sym = symbol.upper()
    if sym in SYMBOL_TO_BINANCE:
        depth = binance_depth(sym, limit=20)
        trades = binance_agg_trades(sym)
        if depth and trades:
            buys = sum(t["qty"] for t in trades if t["side"] == "buy")
            sells = sum(t["qty"] for t in trades if t["side"] == "sell")
            return {
                "symbol": sym, "type": "crypto_l2",
                "depth": depth, "recent_trades_count": len(trades),
                "buy_volume": round(buys, 4), "sell_volume": round(sells, 4),
                "imbalance_pct": round((buys - sells) / (buys + sells + 1e-9) * 100, 2),
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "binance",
            }
    # Fallback: OHLCV-based reconstruction
    if df is not None:
        return {**reconstruct_order_flow(df), "symbol": sym, "type": "ohlcv_proxy"}
    return {"symbol": sym, "type": "unavailable"}
