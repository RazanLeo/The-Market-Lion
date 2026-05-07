"""Volume Charts School — each bar = fixed cumulative volume bin.

Bin size = avg(volume of last 20 bars). Aggregate price within bin to form OHLC.
Detect trend on the resulting volume-bar series (ROC + slope).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "volume_charts_school"
WEIGHT_DEFAULT = 0.65


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    avg_v = float(df["v"].rolling(20).mean().iloc[-1] or 1)
    bin_size = avg_v
    cum = 0.0; bars: list[dict] = []
    cur = {"o": None, "h": -1e18, "l": 1e18, "c": None}
    for _, row in df.iterrows():
        v = float(row["v"] or 0)
        if cur["o"] is None: cur["o"] = float(row["o"])
        cur["h"] = max(cur["h"], float(row["h"]))
        cur["l"] = min(cur["l"], float(row["l"]))
        cur["c"] = float(row["c"])
        cum += v
        if cum >= bin_size:
            bars.append(cur); cum = 0
            cur = {"o": float(row["c"]), "h": float(row["h"]), "l": float(row["l"]), "c": float(row["c"])}
    if cur["o"] is not None: bars.append(cur)
    if len(bars) < 10:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    closes = [b["c"] for b in bars[-30:]]
    roc = (closes[-1] - closes[0]) / closes[0] * 100 if closes[0] else 0
    payload = {"vol_bars_count": len(bars), "vol_bin_size": round(bin_size, 2),
               "vol_chart_roc_pct": round(roc, 2)}
    if roc > 1: return AnalyzerResult(CODE, "buy", min(60.0, 35 + abs(roc) * 3), WEIGHT_DEFAULT, payload)
    if roc < -1: return AnalyzerResult(CODE, "sell", min(60.0, 35 + abs(roc) * 3), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class VolumeChartsSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
