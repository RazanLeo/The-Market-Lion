"""Mitigation Block (ICT) — origin candle of a manipulation move acts as mitigation when retested.

Detect: a liquidity sweep (wick beyond a recent swing) followed by ≥2× ATR opposite move,
the *origin candle* of that opposite leg is the mitigation block.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "mitigation_block_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    last_close = float(df["c"].iloc[-1])
    # Scan backward 30 bars for sweep+reversal
    mitigations: list[dict] = []
    for i in range(len(df) - 8, max(len(df) - 50, 5), -1):
        win_pre = df.iloc[max(i - 20, 0):i]
        if len(win_pre) < 10: continue
        # Sweep above
        if df["h"].iloc[i] > float(win_pre["h"].max()) and df["c"].iloc[i] < float(win_pre["h"].max()):
            # Move opposite ≥ 2×ATR within next 10 bars
            move = float(df["c"].iloc[i + 1:i + 11].min()) - df["c"].iloc[i] if i + 1 < len(df) else 0
            if move <= -2 * atr:
                # Origin candle = the highest-high candle in the sweep formation
                origin_idx = int(df["h"].iloc[max(i - 3, 0):i + 1].argmax()) + max(i - 3, 0)
                mitigations.append({"side": "bearish", "high": float(df["h"].iloc[origin_idx]),
                                    "low": float(df["l"].iloc[origin_idx]), "bar": origin_idx})
        if df["l"].iloc[i] < float(win_pre["l"].min()) and df["c"].iloc[i] > float(win_pre["l"].min()):
            move = float(df["c"].iloc[i + 1:i + 11].max()) - df["c"].iloc[i] if i + 1 < len(df) else 0
            if move >= 2 * atr:
                origin_idx = int(df["l"].iloc[max(i - 3, 0):i + 1].argmin()) + max(i - 3, 0)
                mitigations.append({"side": "bullish", "high": float(df["h"].iloc[origin_idx]),
                                    "low": float(df["l"].iloc[origin_idx]), "bar": origin_idx})
    if not mitigations:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    nearest = min(mitigations, key=lambda z: abs(((z["high"] + z["low"]) / 2) - last_close))
    in_zone = nearest["low"] - atr * 0.2 <= last_close <= nearest["high"] + atr * 0.2
    payload = {"side": nearest["side"], "high": round(nearest["high"], 5),
               "low": round(nearest["low"], 5), "bar": nearest["bar"], "in_zone": in_zone}
    if not in_zone:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)
    if nearest["side"] == "bullish":
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)


class MitigationBlockSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
