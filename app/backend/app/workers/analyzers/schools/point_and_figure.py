"""Point & Figure — ATR-based box size + 3-box reversal + classic patterns."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "point_and_figure"
WEIGHT_DEFAULT = 0.9


def _build_pf(closes, box: float, reversal_boxes: int = 3):
    if not closes or box <= 0: return []
    cols = []; cur_dir, cur = "X", [closes[0]]; last = closes[0]
    for p in closes[1:]:
        if cur_dir == "X":
            if p >= last + box:
                steps = int((p - last) // box)
                for _ in range(steps): cur.append(cur[-1] + box)
                last = cur[-1]
            elif p <= last - reversal_boxes * box:
                cols.append((cur_dir, cur)); cur_dir = "O"
                steps = int((last - p) // box); cur = [last - box * i for i in range(1, steps + 1)]
                last = cur[-1]
        else:
            if p <= last - box:
                steps = int((last - p) // box)
                for _ in range(steps): cur.append(cur[-1] - box)
                last = cur[-1]
            elif p >= last + reversal_boxes * box:
                cols.append((cur_dir, cur)); cur_dir = "X"
                steps = int((p - last) // box); cur = [last + box * i for i in range(1, steps + 1)]
                last = cur[-1]
    cols.append((cur_dir, cur))
    return cols


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 0)
    last = float(df["c"].iloc[-1])
    box = max(atr * 0.3, last * 0.003)
    if box <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    cols = _build_pf(df["c"].tolist(), box)
    if len(cols) < 3:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"cols": len(cols)})
    last_col = cols[-1]
    cur_dir, cur_levels = last_col
    cur_max = max(cur_levels); cur_min = min(cur_levels)
    prior_same = next((col for col in reversed(cols[:-1]) if col[0] == cur_dir), None)
    same_max = max(prior_same[1]) if prior_same else None
    same_min = min(prior_same[1]) if prior_same else None

    pattern = None
    if cur_dir == "X" and same_max and cur_max > same_max: pattern = "double_top_buy"
    if cur_dir == "O" and same_min and cur_min < same_min: pattern = "double_bottom_sell"

    same_dir_cols = [col for col in cols if col[0] == cur_dir][-3:]
    if len(same_dir_cols) >= 3 and pattern == "double_top_buy":
        if max(same_dir_cols[0][1]) < max(same_dir_cols[1][1]) < max(same_dir_cols[2][1]):
            pattern = "triple_top_buy"
    if len(same_dir_cols) >= 3 and pattern == "double_bottom_sell":
        if min(same_dir_cols[0][1]) > min(same_dir_cols[1][1]) > min(same_dir_cols[2][1]):
            pattern = "triple_bottom_sell"

    target = None
    if pattern in ("double_top_buy", "triple_top_buy"):
        target = cur_max + len(cur_levels) * box
    elif pattern in ("double_bottom_sell", "triple_bottom_sell"):
        target = cur_min - len(cur_levels) * box

    payload = {"box_size": round(box, 5), "columns": len(cols),
               "current_direction": cur_dir, "column_size": len(cur_levels),
               "current_max": round(cur_max, 5), "current_min": round(cur_min, 5),
               "prior_same_max": round(same_max, 5) if same_max else None,
               "prior_same_min": round(same_min, 5) if same_min else None,
               "pattern": pattern, "vertical_target": round(target, 5) if target else None}
    if pattern == "triple_top_buy": return AnalyzerResult(CODE, "buy", 80.0, WEIGHT_DEFAULT, payload)
    if pattern == "triple_bottom_sell": return AnalyzerResult(CODE, "sell", 80.0, WEIGHT_DEFAULT, payload)
    if pattern == "double_top_buy": return AnalyzerResult(CODE, "buy", 65.0, WEIGHT_DEFAULT, payload)
    if pattern == "double_bottom_sell": return AnalyzerResult(CODE, "sell", 65.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class PointAndFigureAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
