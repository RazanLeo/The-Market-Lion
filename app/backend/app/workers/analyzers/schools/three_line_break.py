"""Three-Line Break (TLB) — new top line drawn when close > prior 3 line-tops.

Reversal: close < prior 3 line-bottoms (and mirror).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "three_line_break"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    closes = df["c"].tolist()
    lines: list[tuple[float, float, str]] = []  # (top, bottom, color)
    cur_top = closes[0]; cur_bot = closes[0]; cur_color = "white"
    for p in closes[1:]:
        # White = up; Black = down
        if cur_color in ("white",) and p > cur_top:
            lines.append((cur_top, cur_bot, "white"))
            cur_bot = cur_top; cur_top = p
        elif cur_color == "white":
            recent_bots = [ln[1] for ln in lines[-3:]]
            if len(recent_bots) >= 3 and p < min(recent_bots):
                lines.append((cur_top, cur_bot, "white"))
                cur_color = "black"; cur_top = cur_bot; cur_bot = p
        elif cur_color == "black" and p < cur_bot:
            lines.append((cur_top, cur_bot, "black"))
            cur_top = cur_bot; cur_bot = p
        elif cur_color == "black":
            recent_tops = [ln[0] for ln in lines[-3:]]
            if len(recent_tops) >= 3 and p > max(recent_tops):
                lines.append((cur_top, cur_bot, "black"))
                cur_color = "white"; cur_bot = cur_top; cur_top = p
    payload = {"current_color": cur_color, "lines_count": len(lines),
               "current_top": round(cur_top, 5), "current_bottom": round(cur_bot, 5)}
    if cur_color == "white" and len(lines) >= 3:
        return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    if cur_color == "black" and len(lines) >= 3:
        return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class ThreeLineBreakAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
