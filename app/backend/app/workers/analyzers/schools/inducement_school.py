"""Inducement (SMC) — engineered liquidity above/below a minor swing to lure retail.

Detect: a minor swing high (or low) within last 30 bars gets swept (wick beyond it),
followed by an opposing move > 2×ATR within 10 bars. That swept level was the inducement.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "inducement_school"
WEIGHT_DEFAULT = 1.0


def _minor_swings(df: pd.DataFrame, n: int = 3):
    pivs = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivs.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivs.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivs)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    pivs = _minor_swings(df, 3)
    if len(pivs) < 4:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    inducements: list[dict] = []
    for piv_i, kind, level in pivs[-8:]:
        # search bars after piv_i for a sweep
        after = df.iloc[piv_i + 1:]
        if len(after) < 5: continue
        if kind == "H":
            sweep_idx = None
            for j, val in enumerate(after["h"]):
                if val > level: sweep_idx = j; break
            if sweep_idx is None: continue
            # Check for ≥ 2×ATR drop after sweep within 10 bars
            post = after.iloc[sweep_idx + 1:sweep_idx + 11]
            if len(post) and float(post["c"].min()) < float(after["c"].iloc[sweep_idx]) - 2 * atr:
                inducements.append({"side": "bearish", "level": level, "swept_bar": piv_i + 1 + sweep_idx})
        else:
            sweep_idx = None
            for j, val in enumerate(after["l"]):
                if val < level: sweep_idx = j; break
            if sweep_idx is None: continue
            post = after.iloc[sweep_idx + 1:sweep_idx + 11]
            if len(post) and float(post["c"].max()) > float(after["c"].iloc[sweep_idx]) + 2 * atr:
                inducements.append({"side": "bullish", "level": level, "swept_bar": piv_i + 1 + sweep_idx})
    if not inducements:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last = inducements[-1]
    last_close = float(df["c"].iloc[-1])
    bars_since = len(df) - 1 - last["swept_bar"]
    payload = {"side": last["side"], "swept_level": round(last["level"], 5),
               "swept_bar": last["swept_bar"], "bars_since_sweep": bars_since}
    if bars_since > 12:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    if last["side"] == "bullish":
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)


class InducementSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
