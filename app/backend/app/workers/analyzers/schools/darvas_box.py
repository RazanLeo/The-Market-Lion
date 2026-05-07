"""Darvas Box — identify ceiling-bottom box, breakout long with rising volume.

Ceiling: highest high of the last 3+ bars where no new high made since.
Floor: lowest low subsequently formed without breaching the ceiling.
Long entry: close above ceiling on volume > 1.5× avg. Stop = floor.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "darvas_box"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-25:-3]
    if len(win) < 8: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ceiling = float(win["h"].max()); ceiling_idx = int(win["h"].argmax())
    # Confirm 3 bars after ceiling did not exceed it
    after_ceiling = win.iloc[ceiling_idx + 1:]
    if len(after_ceiling) < 3 or after_ceiling["h"].max() >= ceiling:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    floor = float(after_ceiling["l"].min())
    # 3 bars after floor formation that did not breach floor
    last_close = float(df["c"].iloc[-1])
    last_vol = float(df["v"].iloc[-1])
    avg_vol = float(df["v"].rolling(20).mean().iloc[-1] or 1)
    breakout_up = last_close > ceiling and last_vol > avg_vol * 1.5
    breakdown_dn = last_close < floor and last_vol > avg_vol * 1.5
    payload = {"ceiling": round(ceiling, 5), "floor": round(floor, 5),
               "ceiling_break": breakout_up, "floor_break": breakdown_dn,
               "vol_ratio": round(last_vol / avg_vol, 2)}
    if breakout_up: return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if breakdown_dn: return AnalyzerResult(CODE, "sell", 60, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class DarvasBoxAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
