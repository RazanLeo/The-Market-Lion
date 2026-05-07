"""Three Line Break Chart — reversal needs to break last 3 lines' extreme.

Bullish line continues until close < min of last 3 line lows. Counts current
streak of same-color lines; 4+ = strong trend.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "three_line_break_chart"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    closes = df["c"].iloc[-100:]
    lines = []  # list of (start, end, direction)
    cur_high = float(closes.iloc[0]); cur_low = float(closes.iloc[0])
    cur_dir = 0
    for p in closes.iloc[1:]:
        p = float(p)
        if cur_dir == 0:
            if p > cur_high: lines.append((cur_high, p, +1)); cur_dir = +1; cur_low = cur_high; cur_high = p
            elif p < cur_low: lines.append((cur_low, p, -1)); cur_dir = -1; cur_high = cur_low; cur_low = p
        elif cur_dir == +1:
            if p > cur_high: lines.append((cur_high, p, +1)); cur_low = cur_high; cur_high = p
            elif len(lines) >= 3 and p < min(l[0] for l in lines[-3:]):
                lines.append((cur_high, p, -1)); cur_dir = -1; cur_low = p
        elif cur_dir == -1:
            if p < cur_low: lines.append((cur_low, p, -1)); cur_high = cur_low; cur_low = p
            elif len(lines) >= 3 and p > max(l[0] for l in lines[-3:]):
                lines.append((cur_low, p, +1)); cur_dir = +1; cur_high = p
    if len(lines) < 3:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"n_lines": len(lines)})
    # streak
    streak = 1
    for i in range(len(lines) - 2, -1, -1):
        if lines[i][2] == lines[-1][2]: streak += 1
        else: break
    payload = {"n_lines": len(lines), "current_dir": "white" if lines[-1][2] == +1 else "black",
               "streak": streak}
    if lines[-1][2] == +1 and streak >= 4:
        return AnalyzerResult(CODE, "buy", min(75, 50 + streak * 5), WEIGHT_DEFAULT, payload)
    if lines[-1][2] == -1 and streak >= 4:
        return AnalyzerResult(CODE, "sell", min(75, 50 + streak * 5), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class ThreeLineBreakChartAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
