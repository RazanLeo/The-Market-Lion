"""Market Lion — DeMark Sequential + TD Combo.
TD Sequential: Setup (9 bars) + Countdown (13 bars) → exhaustion signals.
TD Combo: Alternative exhaustion indicator.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeMarkResult:
    td_buy_setup: Optional[int]    # bar count 1-9 (9 = complete setup)
    td_sell_setup: Optional[int]
    td_buy_countdown: Optional[int]  # 1-13 (13 = exhaustion)
    td_sell_countdown: Optional[int]
    buy_signal: bool
    sell_signal: bool
    setup_bar: int
    countdown_bar: int
    risk_level: Optional[float]


def td_sequential(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> DeMarkResult:
    """
    TD Sequential by Tom DeMark.
    Buy Setup: 9 consecutive closes < close 4 bars ago.
    Sell Setup: 9 consecutive closes > close 4 bars ago.
    """
    n = len(closes)
    if n < 20:
        return DeMarkResult(None, None, None, None, False, False, 0, 0, None)

    # TD Price Flip detection
    def price_flip_buy(i):
        return closes[i] < closes[i - 4] and closes[i - 1] > closes[i - 5]

    def price_flip_sell(i):
        return closes[i] > closes[i - 4] and closes[i - 1] < closes[i - 5]

    # Setup phase
    buy_setup_count = 0
    sell_setup_count = 0
    buy_setup_complete = False
    sell_setup_complete = False
    buy_setup_9_idx = None
    sell_setup_9_idx = None

    for i in range(4, n):
        if closes[i] < closes[i - 4]:
            buy_setup_count += 1
            sell_setup_count = 0
        elif closes[i] > closes[i - 4]:
            sell_setup_count += 1
            buy_setup_count = 0
        else:
            buy_setup_count = 0
            sell_setup_count = 0

        if buy_setup_count == 9:
            buy_setup_complete = True
            buy_setup_9_idx = i
        if sell_setup_count == 9:
            sell_setup_complete = True
            sell_setup_9_idx = i

    # Countdown phase (simplified — needs setup completion first)
    buy_countdown = 0
    sell_countdown = 0
    buy_signal = False
    sell_signal = False
    risk_level = None

    if buy_setup_complete and buy_setup_9_idx:
        # Count bars where close <= low 2 bars ago
        for i in range(buy_setup_9_idx, n):
            if i >= 2 and closes[i] <= lows[i - 2]:
                buy_countdown += 1
                if buy_countdown >= 13:
                    buy_signal = True
                    risk_level = float(np.max(highs[max(0, i - 9):i + 1]))
                    break

    if sell_setup_complete and sell_setup_9_idx:
        # Count bars where close >= high 2 bars ago
        for i in range(sell_setup_9_idx, n):
            if i >= 2 and closes[i] >= highs[i - 2]:
                sell_countdown += 1
                if sell_countdown >= 13:
                    sell_signal = True
                    risk_level = float(np.min(lows[max(0, i - 9):i + 1]))
                    break

    return DeMarkResult(
        td_buy_setup=min(buy_setup_count, 9),
        td_sell_setup=min(sell_setup_count, 9),
        td_buy_countdown=buy_countdown if buy_setup_complete else None,
        td_sell_countdown=sell_countdown if sell_setup_complete else None,
        buy_signal=buy_signal,
        sell_signal=sell_signal,
        setup_bar=max(buy_setup_count, sell_setup_count),
        countdown_bar=max(buy_countdown, sell_countdown),
        risk_level=risk_level,
    )


def td_combo(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> dict:
    """TD Combo — alternative exhaustion pattern."""
    n = len(closes)
    if n < 13:
        return {"signal": "NEUTRAL", "count": 0}

    buy_count = 0
    sell_count = 0

    for i in range(2, n):
        # Buy combo: close < close[i-2] AND close < close[i-1]
        if closes[i] < closes[i - 2] and closes[i] < closes[i - 1]:
            buy_count += 1
            sell_count = 0
        elif closes[i] > closes[i - 2] and closes[i] > closes[i - 1]:
            sell_count += 1
            buy_count = 0
        else:
            buy_count = 0
            sell_count = 0

    if buy_count >= 13:
        return {"signal": "BUY", "count": buy_count, "exhaustion": True}
    elif sell_count >= 13:
        return {"signal": "SELL", "count": sell_count, "exhaustion": True}
    elif buy_count >= 9:
        return {"signal": "BUY_SETUP", "count": buy_count, "exhaustion": False}
    elif sell_count >= 9:
        return {"signal": "SELL_SETUP", "count": sell_count, "exhaustion": False}

    return {"signal": "NEUTRAL", "count": max(buy_count, sell_count)}
