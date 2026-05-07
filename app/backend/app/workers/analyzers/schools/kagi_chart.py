"""Kagi Chart School — yang/yin reversals on Kagi line.

Pure direction-only chart. Reversal threshold = 2% of close. Counts yang vs yin
segments in last 100 closes; majority direction = trend bias.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "kagi_chart"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    threshold = float(df["c"].iloc[-1]) * 0.02
    closes = df["c"].iloc[-100:] if len(df) >= 100 else df["c"]
    if len(closes) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    cur_dir = +1 if float(closes.iloc[1]) > float(closes.iloc[0]) else -1
    cur_extreme = float(closes.iloc[0])
    yang = yin = 0
    for p in closes.iloc[1:]:
        p = float(p)
        if cur_dir == +1:
            if p > cur_extreme: cur_extreme = p
            elif cur_extreme - p >= threshold:
                yang += 1; cur_dir = -1; cur_extreme = p
        else:
            if p < cur_extreme: cur_extreme = p
            elif p - cur_extreme >= threshold:
                yin += 1; cur_dir = +1; cur_extreme = p
    payload = {"yang_segments": yang, "yin_segments": yin,
               "current_direction": "yang" if cur_dir == +1 else "yin",
               "threshold_2pct": round(threshold, 5)}
    if cur_dir == +1 and yang >= yin + 2:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if cur_dir == -1 and yin >= yang + 2:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class KagiChartAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
