"""Smart Money Concepts — BOS, CHoCH, Order Blocks, Fair Value Gaps, Liquidity sweeps.

Definitions used:
  • Swing high/low: fractal-of-3 (price beats neighbors on both sides for 3 bars).
  • BOS (Break of Structure): close beyond previous swing high (bullish) or low (bearish).
  • CHoCH (Change of Character): the FIRST BOS that goes against the prior structural direction.
  • Order Block (OB): the last opposing candle before the impulse leg that produced a BOS.
       Bullish OB = last bearish candle before strong rally.
       Bearish OB = last bullish candle before strong drop.
  • Fair Value Gap (FVG): 3-candle pattern where candle[i-2].high < candle[i].low (bullish FVG)
       or candle[i-2].low > candle[i].high (bearish FVG).
  • Liquidity Sweep: wick beyond a recent equal-high/low cluster, then close back inside.
"""
from __future__ import annotations
from typing import Any
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "smc"
WEIGHT_DEFAULT = 1.5


def _swings(df: pd.DataFrame, n: int = 3):
    highs, lows = [], []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            highs.append(i)
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            lows.append(i)
    return highs, lows


def _detect_fvg(df: pd.DataFrame, lookback: int = 30) -> dict | None:
    """Return most-recent unmitigated FVG."""
    last = len(df) - 1
    for i in range(last, max(last - lookback, 2), -1):
        prev2_h = df["h"].iloc[i - 2]; prev2_l = df["l"].iloc[i - 2]
        cur_h = df["h"].iloc[i]; cur_l = df["l"].iloc[i]
        # Bullish FVG: gap up — current low > prev2 high
        if cur_l > prev2_h:
            mitigated = (df["l"].iloc[i + 1:].min() if i + 1 < len(df) else cur_l) <= prev2_h
            return {"type": "bullish_fvg", "low": float(prev2_h), "high": float(cur_l), "bar": int(i), "mitigated": bool(mitigated)}
        if cur_h < prev2_l:
            mitigated = (df["h"].iloc[i + 1:].max() if i + 1 < len(df) else cur_h) >= prev2_l
            return {"type": "bearish_fvg", "low": float(cur_h), "high": float(prev2_l), "bar": int(i), "mitigated": bool(mitigated)}
    return None


def _detect_order_block(df: pd.DataFrame, swings_high: list[int], swings_low: list[int]) -> dict | None:
    """Return most-recent unmitigated OB before a BOS."""
    if len(df) < 30:
        return None
    last_close = df["c"].iloc[-1]
    # Bullish OB: scan backwards for a bearish candle followed by ≥3 bullish candles that broke a swing high
    for i in range(len(df) - 5, max(len(df) - 60, 1), -1):
        if df["c"].iloc[i] < df["o"].iloc[i]:  # bearish candle
            # Did the next 3-5 candles produce a fresh high above the most recent prior swing high?
            highs_after = df["h"].iloc[i + 1:i + 6]
            prior_high = df["h"].iloc[max(i - 10, 0):i].max() if i > 0 else df["h"].iloc[i]
            if highs_after.max() > prior_high:
                ob_high = float(df["h"].iloc[i]); ob_low = float(df["l"].iloc[i])
                # mitigated if price has revisited and gone below ob_low after creation
                mitigated = bool(df["l"].iloc[i + 1:].min() < ob_low)
                if not mitigated and last_close > ob_low:
                    return {"type": "bullish_ob", "low": ob_low, "high": ob_high, "bar": int(i)}
        if df["c"].iloc[i] > df["o"].iloc[i]:  # bullish candle (potential bearish OB)
            lows_after = df["l"].iloc[i + 1:i + 6]
            prior_low = df["l"].iloc[max(i - 10, 0):i].min() if i > 0 else df["l"].iloc[i]
            if lows_after.min() < prior_low:
                ob_high = float(df["h"].iloc[i]); ob_low = float(df["l"].iloc[i])
                mitigated = bool(df["h"].iloc[i + 1:].max() > ob_high)
                if not mitigated and last_close < ob_high:
                    return {"type": "bearish_ob", "low": ob_low, "high": ob_high, "bar": int(i)}
    return None


def _detect_sweep(df: pd.DataFrame) -> dict | None:
    """Liquidity sweep: wick beyond cluster of equal highs/lows, then close back inside."""
    last = df.iloc[-1]
    win = df.iloc[-30:-1]
    if len(win) < 10:
        return None
    eq_high = float(win["h"].max())
    eq_low = float(win["l"].min())
    if last["h"] > eq_high and last["c"] < eq_high:
        return {"type": "BSL_sweep", "level": eq_high}
    if last["l"] < eq_low and last["c"] > eq_low:
        return {"type": "SSL_sweep", "level": eq_low}
    return None


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    swings_high, swings_low = _swings(df, 3)
    if len(swings_high) < 2 or len(swings_low) < 2:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    last_close = float(df["c"].iloc[-1])
    last_swing_high = float(df["h"].iloc[swings_high[-1]])
    prev_swing_high = float(df["h"].iloc[swings_high[-2]])
    last_swing_low = float(df["l"].iloc[swings_low[-1]])
    prev_swing_low = float(df["l"].iloc[swings_low[-2]])

    bos_up = last_close > prev_swing_high
    bos_down = last_close < prev_swing_low
    structure_bull = last_swing_high > prev_swing_high and last_swing_low > prev_swing_low
    structure_bear = last_swing_high < prev_swing_high and last_swing_low < prev_swing_low

    # CHoCH = BOS opposite to prior structure
    choch_up = bos_up and structure_bear
    choch_down = bos_down and structure_bull

    fvg = _detect_fvg(df)
    ob = _detect_order_block(df, swings_high, swings_low)
    sweep = _detect_sweep(df)

    payload: dict[str, Any] = {
        "structure": "HH+HL" if structure_bull else "LL+LH" if structure_bear else "mixed",
        "bos_up": bos_up, "bos_down": bos_down,
        "choch_up": choch_up, "choch_down": choch_down,
        "last_swing_high": round(last_swing_high, 5),
        "last_swing_low": round(last_swing_low, 5),
        "fvg": fvg, "order_block": ob, "sweep": sweep,
    }

    score = 0.0
    if choch_up: score += 35
    elif bos_up and structure_bull: score += 25
    if choch_down: score -= 35
    elif bos_down and structure_bear: score -= 25

    if ob and ob["type"] == "bullish_ob" and last_close > ob["low"]: score += 15
    if ob and ob["type"] == "bearish_ob" and last_close < ob["high"]: score -= 15
    if fvg and fvg["type"] == "bullish_fvg" and not fvg["mitigated"]: score += 8
    if fvg and fvg["type"] == "bearish_fvg" and not fvg["mitigated"]: score -= 8
    if sweep and sweep["type"] == "SSL_sweep": score += 18
    if sweep and sweep["type"] == "BSL_sweep": score -= 18

    if score >= 20:
        return AnalyzerResult(CODE, "buy", min(90.0, 50 + score), WEIGHT_DEFAULT, payload)
    if score <= -20:
        return AnalyzerResult(CODE, "sell", min(90.0, 50 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class SmcAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
