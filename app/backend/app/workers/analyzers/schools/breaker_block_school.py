"""Breaker Block (ICT) — an Order Block that fails (price breaks back through) becomes the opposite-side zone.

  Bullish OB violated (close below its low) → becomes BEARISH BREAKER on retest from below.
  Bearish OB violated (close above its high) → becomes BULLISH BREAKER on retest from above.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "breaker_block_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_close = float(df["c"].iloc[-1])
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    # Look back for OBs (last opposing candle before strong move)
    breaker_zones: list[dict] = []
    for i in range(len(df) - 5, max(len(df) - 80, 1), -1):
        # Bullish OB candidate at i
        if df["c"].iloc[i] < df["o"].iloc[i]:
            highs_after = df["h"].iloc[i + 1:i + 6]
            prior_high = df["h"].iloc[max(i - 10, 0):i].max() if i > 0 else df["h"].iloc[i]
            if len(highs_after) and highs_after.max() > prior_high:
                ob_high = float(df["h"].iloc[i]); ob_low = float(df["l"].iloc[i])
                # Was the bullish OB violated later?
                violation = df["c"].iloc[i + 1:].min() < ob_low if i + 1 < len(df) else False
                if violation:
                    breaker_zones.append({"side": "bearish_breaker", "high": ob_high, "low": ob_low, "bar": i})
        if df["c"].iloc[i] > df["o"].iloc[i]:
            lows_after = df["l"].iloc[i + 1:i + 6]
            prior_low = df["l"].iloc[max(i - 10, 0):i].min() if i > 0 else df["l"].iloc[i]
            if len(lows_after) and lows_after.min() < prior_low:
                ob_high = float(df["h"].iloc[i]); ob_low = float(df["l"].iloc[i])
                violation = df["c"].iloc[i + 1:].max() > ob_high if i + 1 < len(df) else False
                if violation:
                    breaker_zones.append({"side": "bullish_breaker", "high": ob_high, "low": ob_low, "bar": i})

    if not breaker_zones:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    # Most recent breaker
    nearest = min(breaker_zones, key=lambda z: abs(((z["high"] + z["low"]) / 2) - last_close))
    in_zone = nearest["low"] - atr * 0.2 <= last_close <= nearest["high"] + atr * 0.2
    payload = {"side": nearest["side"], "high": round(nearest["high"], 5),
               "low": round(nearest["low"], 5), "bar": nearest["bar"], "in_zone": in_zone}
    if not in_zone:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    if nearest["side"] == "bullish_breaker":
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)


class BreakerBlockSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
