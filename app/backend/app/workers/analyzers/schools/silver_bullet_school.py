"""ICT Silver Bullet — 15-minute window after killzone open with high-prob MSS setup.

Windows (UTC):
  • 14:00 – 14:15 UTC (10:00 AM NY) — primary Silver Bullet.
  • 18:00 – 18:15 UTC (2:00 PM NY) — afternoon Silver Bullet.
Setup: liquidity sweep (wick beyond recent swing) + Fair Value Gap formed in window + reversal candle.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "silver_bullet_school"
WEIGHT_DEFAULT = 0.95


def _detect_fvg(window: pd.DataFrame) -> dict | None:
    if len(window) < 3: return None
    for i in range(2, len(window)):
        prev2_h = window["h"].iloc[i - 2]; prev2_l = window["l"].iloc[i - 2]
        cur_h = window["h"].iloc[i]; cur_l = window["l"].iloc[i]
        if cur_l > prev2_h:
            return {"type": "bull_fvg", "low": float(prev2_h), "high": float(cur_l)}
        if cur_h < prev2_l:
            return {"type": "bear_fvg", "low": float(cur_h), "high": float(prev2_l)}
    return None


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_ts = df.index[-1]
    today = last_ts.normalize()
    sb_windows = [
        (today + pd.Timedelta(hours=14), today + pd.Timedelta(hours=14, minutes=15), "AM_SB"),
        (today + pd.Timedelta(hours=18), today + pd.Timedelta(hours=18, minutes=15), "PM_SB"),
    ]
    setups = []
    for s, e, name in sb_windows:
        in_win = df[(df.index >= s) & (df.index <= e)]
        if len(in_win) < 2: continue
        # Pre-window swing reference
        pre = df[(df.index >= s - pd.Timedelta(hours=2)) & (df.index < s)]
        if len(pre) < 5: continue
        sweep_high = float(in_win["h"].max()) > float(pre["h"].max())
        sweep_low = float(in_win["l"].min()) < float(pre["l"].min())
        fvg = _detect_fvg(in_win)
        last_close = float(df["c"].iloc[-1])
        if sweep_high and fvg and fvg["type"] == "bear_fvg":
            setups.append({"window": name, "side": "sell", "fvg": fvg})
        if sweep_low and fvg and fvg["type"] == "bull_fvg":
            setups.append({"window": name, "side": "buy", "fvg": fvg})
    if not setups:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_setup = setups[-1]
    payload = {"setups": setups}
    if last_setup["side"] == "buy": return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)


class SilverBulletSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
