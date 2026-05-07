"""Range Bars Chart — each constructed bar = 1×ATR price range.

Walk through closes; whenever cumulative move exceeds the range size, emit a new bar.
Count consecutive same-direction range bars.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "range_bars_chart_school"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 0)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rng = atr  # 1×ATR
    bars: list[int] = []
    base = float(df["c"].iloc[0])
    for p in df["c"].iloc[1:]:
        diff = float(p) - base
        if abs(diff) >= rng:
            steps = int(abs(diff) // rng)
            sgn = 1 if diff > 0 else -1
            for _ in range(steps): bars.append(sgn)
            base += sgn * steps * rng
    if len(bars) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    streak = 1
    cur = bars[-1]
    for i in range(2, min(len(bars), 30)):
        if bars[-i] == cur: streak += 1
        else: break
    reversal = streak == 1 and len(bars) > 4 and all(b == -cur for b in bars[-5:-1])
    payload = {"range_size": round(rng, 5), "total_bars": len(bars),
               "current_color": "up" if cur > 0 else "down",
               "streak": streak, "reversal_flag": reversal}
    if reversal: return AnalyzerResult(CODE, "buy" if cur > 0 else "sell", 65, WEIGHT_DEFAULT, payload)
    if streak >= 5:
        side = "buy" if cur > 0 else "sell"
        return AnalyzerResult(CODE, side, min(80.0, 45 + streak * 4), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class RangeBarsChartSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
