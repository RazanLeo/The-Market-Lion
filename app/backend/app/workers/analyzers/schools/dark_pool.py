"""Dark Pool — proxy detection via volume/range anomalies.

Dark prints typically show up as: HUGE volume but TINY price range
(off-spread executions absorbed without moving market).
We flag bars where vol > 2.5× avg AND range < 0.5× avg AND body < 0.3× range.
The trade direction is inferred from the next 3 bars' close drift.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "dark_pool"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    v = df["v"].fillna(0)
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    body = (df["c"] - df["o"]).abs()
    avg_v = v.rolling(50).mean()
    avg_r = rng.rolling(50).mean()
    dark = (v > avg_v * 2.5) & (rng < avg_r * 0.5) & (body < rng * 0.3)
    last_dark_idx = None
    for i in range(len(df) - 1, max(len(df) - 30, 0), -1):
        if bool(dark.iloc[i]):
            last_dark_idx = i; break
    if last_dark_idx is None:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    bars_since = len(df) - 1 - last_dark_idx
    after = df.iloc[last_dark_idx + 1:last_dark_idx + 4]
    direction_after = "up" if len(after) and after["c"].iloc[-1] > df["c"].iloc[last_dark_idx] else "down"
    intensity = float(v.iloc[last_dark_idx] / (avg_v.iloc[last_dark_idx] or 1))
    payload = {"dark_print_bar": last_dark_idx, "bars_since": bars_since,
               "intensity_x": round(intensity, 2),
               "direction_after_print": direction_after,
               "dark_print_price": round(float(df["c"].iloc[last_dark_idx]), 5)}
    if bars_since > 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    if direction_after == "up": return AnalyzerResult(CODE, "buy", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)


class DarkPoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
