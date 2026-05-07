"""Tick Chart School — aggregate every N (=100) bars into one tick-bar (volume as proxy).

Build OHLC of tick-bars from the underlying time-bars by accumulating volume.
Trend on tick-bar ROC.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "tick_chart_school"
WEIGHT_DEFAULT = 0.65


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    avg_v = float(df["v"].rolling(20).mean().iloc[-1] or 1)
    bin_size = max(avg_v, 1) * 5  # 5x avg volume per tick-bar
    cum = 0.0; bars: list[dict] = []
    cur = {"o": None, "h": -1e18, "l": 1e18, "c": None, "v": 0.0}
    for _, row in df.iterrows():
        v = float(row["v"] or 0); price = float(row["c"])
        if cur["o"] is None: cur["o"] = price
        cur["h"] = max(cur["h"], float(row["h"]))
        cur["l"] = min(cur["l"], float(row["l"]))
        cur["c"] = price
        cur["v"] += v; cum += v
        if cum >= bin_size:
            bars.append(cur); cum = 0
            cur = {"o": price, "h": float(row["h"]), "l": float(row["l"]), "c": price, "v": 0.0}
    if cur["o"] is not None: bars.append(cur)
    if len(bars) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    closes = [b["c"] for b in bars]
    roc = (closes[-1] - closes[-5]) / closes[-5] * 100 if closes[-5] else 0
    payload = {"tick_bars_count": len(bars), "tick_roc_5_pct": round(roc, 2),
               "tick_bin_size": round(bin_size, 2)}
    if roc > 0.5: return AnalyzerResult(CODE, "buy", min(60.0, 35 + abs(roc) * 4), WEIGHT_DEFAULT, payload)
    if roc < -0.5: return AnalyzerResult(CODE, "sell", min(60.0, 35 + abs(roc) * 4), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class TickChartSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
