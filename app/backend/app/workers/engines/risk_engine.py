"""Risk engine — builds full trade plan from balance + risk% + symbol + side.

Implements: position sizing, leverage selection, R-multiple targets (1:1, 1:2, 1:3, 1:5 final),
ATR-based SL distance, trailing rules.
"""
from __future__ import annotations
import asyncio
from typing import Any
import pandas as pd
import numpy as np

from ...services.brokers.capital import CapitalAdapter


PIP_SIZE = {  # symbol -> pip size in price units
    "XAUUSD": 0.1,
    "XAGUSD": 0.01,
    "USOIL": 0.01,
    "BRENT": 0.01,
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "USDJPY": 0.01,
    "USDCHF": 0.0001,
    "AUDUSD": 0.0001,
    "NZDUSD": 0.0001,
    "USDCAD": 0.0001,
}

CONTRACT_SIZE = {  # standard lot
    "XAUUSD": 100, "XAGUSD": 5000, "USOIL": 1000, "BRENT": 1000,
    "EURUSD": 100000, "GBPUSD": 100000, "USDJPY": 100000, "USDCHF": 100000,
    "AUDUSD": 100000, "NZDUSD": 100000, "USDCAD": 100000,
}


def _ohlcv_to_df(prices: list[dict[str, Any]]) -> pd.DataFrame:
    """Capital.com price object -> OHLCV DataFrame."""
    rows = []
    for p in prices:
        c = p.get("closePrice", {})
        rows.append({
            "ts": p.get("snapshotTimeUTC"),
            "o": float(p.get("openPrice", {}).get("bid", 0)),
            "h": float(p.get("highPrice", {}).get("bid", 0)),
            "l": float(p.get("lowPrice", {}).get("bid", 0)),
            "c": float(c.get("bid", 0)),
            "v": float(p.get("lastTradedVolume") or 0),
        })
    df = pd.DataFrame(rows)
    if df.empty: return df
    df["ts"] = pd.to_datetime(df["ts"])
    return df.set_index("ts").sort_index()


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    if len(df) < period + 1: return float(df["c"].iloc[-1] * 0.005) if len(df) else 1.0
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def _select_leverage(balance: float) -> int:
    if balance < 1000: return 30
    if balance < 10_000: return 100
    if balance < 50_000: return 200
    return 500


def _resolution_for_tf(tf: str) -> str:
    return {
        "1M": "MINUTE", "5M": "MINUTE_5", "15M": "MINUTE_15", "30M": "MINUTE_30",
        "1H": "HOUR", "4H": "HOUR_4", "1D": "DAY", "1W": "WEEK",
    }.get(tf, "MINUTE_15")


async def build_trade_plan(*, symbol: str, side: str, balance: float, risk_pct: float, tf: str, broker: CapitalAdapter) -> dict[str, Any]:
    sym = symbol.upper()
    pip = PIP_SIZE.get(sym, 0.0001)
    contract = CONTRACT_SIZE.get(sym, 100_000)

    # Pull recent prices to compute ATR + last close
    epic = CapitalAdapter._symbol_to_epic(sym)
    prices = await broker.historical_prices(epic, resolution=_resolution_for_tf(tf), max_bars=200)
    df = _ohlcv_to_df(prices)
    last = float(df["c"].iloc[-1]) if not df.empty else 1.0
    atr = _atr(df, 14) or last * 0.005
    sl_distance = max(atr * 1.5, last * 0.001)

    risk_amount = balance * (risk_pct / 100.0)

    if side == "buy":
        entry = last
        sl = last - sl_distance
        tp1 = last + sl_distance
        tp2 = last + 2 * sl_distance
        tp3 = last + 3 * sl_distance
        final_tp = last + 5 * sl_distance
    else:
        entry = last
        sl = last + sl_distance
        tp1 = last - sl_distance
        tp2 = last - 2 * sl_distance
        tp3 = last - 3 * sl_distance
        final_tp = last - 5 * sl_distance

    sl_pips = abs(entry - sl) / pip
    pip_value_per_lot = pip * contract
    lot = max(round(risk_amount / max(sl_pips * pip_value_per_lot, 1e-6), 4), 0.01)

    leverage = _select_leverage(balance)

    return {
        "symbol": sym, "side": side, "tf": tf,
        "entry": round(entry, 5), "sl": round(sl, 5),
        "tp1": round(tp1, 5), "tp2": round(tp2, 5), "tp3": round(tp3, 5), "final_tp": round(final_tp, 5),
        "atr": round(atr, 5), "sl_distance": round(sl_distance, 5), "sl_pips": round(sl_pips, 2),
        "lot": float(lot), "leverage": leverage,
        "risk_pct": risk_pct, "risk_amount": round(risk_amount, 2),
        "expected_profit_at_tp1": round(sl_pips * pip_value_per_lot * lot, 2),
        "expected_loss_at_sl": round(risk_amount, 2),
        "pip_size": pip, "contract_size": contract,
    }


def daily_loss_breach(equity_history: list[float], limit_pct: float) -> bool:
    if not equity_history: return False
    peak = max(equity_history)
    cur = equity_history[-1]
    return ((peak - cur) / peak) * 100 >= limit_pct
