"""Lightweight Backtest + Walk-Forward — minimum viable for showing historical success."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any
import pandas as pd
import numpy as np


@dataclass
class BacktestResult:
    trades: int
    wins: int
    losses: int
    win_rate: float
    profit_factor: float
    total_pnl_r: float
    max_drawdown_r: float
    sharpe_like: float


def run_simple_backtest(df: pd.DataFrame, signal_fn: Callable[[pd.DataFrame], dict]) -> BacktestResult:
    """Walks bar-by-bar, calls signal_fn(df_so_far) → {'side': 'buy'/'sell'/None, 'sl_distance': float}.

    Closes a simulated trade when SL or 2×R TP is hit. R = sl_distance.
    """
    rs: list[float] = []
    open_trade: dict[str, Any] | None = None
    for i in range(50, len(df) - 1):
        sub = df.iloc[: i + 1]
        last = sub["c"].iloc[-1]
        if open_trade:
            # check SL or TP
            side = open_trade["side"]
            entry = open_trade["entry"]
            sl = open_trade["sl"]
            tp = open_trade["tp"]
            high = df["h"].iloc[i + 1]
            low = df["l"].iloc[i + 1]
            if side == "buy":
                if low <= sl:
                    rs.append(-1.0); open_trade = None
                elif high >= tp:
                    rs.append(2.0); open_trade = None
            else:
                if high >= sl:
                    rs.append(-1.0); open_trade = None
                elif low <= tp:
                    rs.append(2.0); open_trade = None
            continue
        sig = signal_fn(sub)
        if sig.get("side") in ("buy", "sell"):
            sld = float(sig.get("sl_distance") or last * 0.005)
            entry = last
            if sig["side"] == "buy":
                sl = entry - sld; tp = entry + 2 * sld
            else:
                sl = entry + sld; tp = entry - 2 * sld
            open_trade = {"side": sig["side"], "entry": entry, "sl": sl, "tp": tp}
    if not rs:
        return BacktestResult(0, 0, 0, 0, 0, 0, 0, 0)
    arr = np.array(rs)
    wins = int((arr > 0).sum()); losses = int((arr < 0).sum())
    pf = arr[arr > 0].sum() / max(abs(arr[arr < 0].sum()), 1e-9)
    eq = arr.cumsum()
    max_dd = float((np.maximum.accumulate(eq) - eq).max())
    sharpe = float(arr.mean() / (arr.std() + 1e-9) * np.sqrt(len(arr)))
    return BacktestResult(
        trades=len(arr), wins=wins, losses=losses,
        win_rate=round(wins / len(arr) * 100, 2),
        profit_factor=round(pf, 2),
        total_pnl_r=round(arr.sum(), 2),
        max_drawdown_r=round(max_dd, 2),
        sharpe_like=round(sharpe, 2),
    )


def walk_forward(df: pd.DataFrame, signal_fn: Callable[[pd.DataFrame], dict],
                 n_windows: int = 4) -> list[BacktestResult]:
    """Splits df into n_windows consecutive segments and runs backtest on each."""
    results = []
    seg = len(df) // (n_windows + 1)
    for k in range(n_windows):
        slc = df.iloc[k * seg : (k + 2) * seg]
        results.append(run_simple_backtest(slc, signal_fn))
    return results
