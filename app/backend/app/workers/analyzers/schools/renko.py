"""Renko bricks — ATR-based brick size + trend brick counting + reversal detection.

Brick size = max(0.5×ATR(14), 0.5% of price).
Reversal brick = brick of opposite color with size ≥ 2× brick size.

The implementation walks closes, generating bricks each time price has moved one full brick.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "renko"
WEIGHT_DEFAULT = 0.85


def _build_bricks(closes: list[float], brick: float) -> list[int]:
    """Return list of +1/-1 bricks. First brick is set when |price - origin| >= brick."""
    if not closes or brick <= 0:
        return []
    bricks: list[int] = []
    origin = closes[0]
    last_brick_close = origin
    direction = 0
    for p in closes[1:]:
        diff = p - last_brick_close
        if direction in (0, 1) and diff >= brick:
            steps = int(diff // brick)
            bricks.extend([1] * steps)
            last_brick_close += steps * brick
            direction = 1
        elif direction in (0, -1) and -diff >= brick:
            steps = int((-diff) // brick)
            bricks.extend([-1] * steps)
            last_brick_close -= steps * brick
            direction = -1
        elif direction == 1 and -diff >= 2 * brick:
            steps = int((-diff) // brick)
            bricks.extend([-1] * steps)
            last_brick_close -= steps * brick
            direction = -1
        elif direction == -1 and diff >= 2 * brick:
            steps = int(diff // brick)
            bricks.extend([1] * steps)
            last_brick_close += steps * brick
            direction = 1
    return bricks


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 0)
    last = float(df["c"].iloc[-1])
    brick = max(atr * 0.5, last * 0.005)
    if brick <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    bricks = _build_bricks(df["c"].tolist(), brick)
    if len(bricks) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"bricks": len(bricks)})

    # Streak of last bricks of the same color
    streak = 1
    last_color = bricks[-1]
    for i in range(2, min(len(bricks), 30)):
        if bricks[-i] == last_color:
            streak += 1
        else:
            break
    # Reversal: 1 opposite brick after long same-color streak
    reversal = streak == 1 and len(bricks) >= 4 and bricks[-2] == -last_color and bricks[-3] == -last_color and bricks[-4] == -last_color

    payload = {
        "brick_size": round(brick, 5), "total_bricks": len(bricks),
        "last_color": "up" if last_color > 0 else "down",
        "streak": streak, "reversal_brick": reversal,
    }

    if reversal:
        return AnalyzerResult(CODE, "buy" if last_color > 0 else "sell", 70.0, WEIGHT_DEFAULT, payload)
    if streak >= 5:
        side = "buy" if last_color > 0 else "sell"
        return AnalyzerResult(CODE, side, min(85.0, 50 + streak * 4), WEIGHT_DEFAULT, payload)
    if streak >= 3:
        side = "buy" if last_color > 0 else "sell"
        return AnalyzerResult(CODE, side, 50.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class RenkoAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
