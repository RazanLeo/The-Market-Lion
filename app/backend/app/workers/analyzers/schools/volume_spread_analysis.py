"""Volume Spread Analysis (Tom Williams / Wyckoff lineage).

Bar classification rules:
  • Spread = high - low.
  • Body = abs(close - open).
  • Close position: c_pos = (close - low) / spread  (0=very low, 1=very high).

Signal recognition (last bar + neighbours):
  1. No Demand   = up bar with narrow spread + below-average volume + close near low.
                   ⇒ no buyers, bearish weakness in an up-move.
  2. No Supply   = down bar with narrow spread + below-average volume + close near high.
                   ⇒ no sellers, bullish strength in a down-move.
  3. Stopping Volume = wide spread + ultra-high volume + close in middle/upper third
                       after a down-trend. ⇒ smart money buying.
  4. Climactic Action  = highest volume of last N bars + wide spread + reversal close.
  5. Effort vs Result  = wide spread but very high volume that produced TINY follow-through next bar.
                         ⇒ failed effort, expect reversal.
  6. Pseudo Upthrust   = wide spread up bar with high volume but close in lower half.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "volume_spread_analysis"
WEIGHT_DEFAULT = 1.25


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    win = df.iloc[-30:].copy()
    win["spread"] = win["h"] - win["l"]
    win["body"] = (win["c"] - win["o"]).abs()
    win["c_pos"] = (win["c"] - win["l"]) / (win["spread"].replace(0, 1e-9))
    avg_spread = float(win["spread"].mean())
    avg_vol = float(win["v"].mean())
    last = win.iloc[-1]
    s = float(last["spread"])
    v = float(last["v"])
    c_pos = float(last["c_pos"])
    close = float(last["c"]); open_p = float(last["o"])

    is_up = close > open_p; is_down = close < open_p
    narrow_spread = s < avg_spread * 0.7
    wide_spread = s > avg_spread * 1.5
    high_vol = v > avg_vol * 1.5
    ultra_vol = v > avg_vol * 2.0
    low_vol = v < avg_vol * 0.7

    # Trend hint over last 10 bars
    trend = "up" if df["c"].iloc[-1] > df["c"].iloc[-11] else "down" if df["c"].iloc[-1] < df["c"].iloc[-11] else "flat"

    signals: list[str] = []
    score = 0.0

    if is_up and narrow_spread and low_vol and c_pos < 0.45:
        signals.append("no_demand"); score -= 30
    if is_down and narrow_spread and low_vol and c_pos > 0.55:
        signals.append("no_supply"); score += 30

    if wide_spread and ultra_vol and c_pos > 0.5 and trend == "down":
        signals.append("stopping_volume_buy"); score += 35
    if wide_spread and ultra_vol and c_pos < 0.5 and trend == "up":
        signals.append("stopping_volume_sell"); score -= 35

    # Climactic
    if v == win["v"].max() and wide_spread:
        if is_up and c_pos < 0.5:
            signals.append("buying_climax"); score -= 25
        if is_down and c_pos > 0.5:
            signals.append("selling_climax"); score += 25

    # Effort vs Result (using prev bar volume vs current bar follow-through)
    if len(win) >= 2:
        prev = win.iloc[-2]
        if float(prev["v"]) > avg_vol * 2 and float(prev["spread"]) > avg_spread * 1.5:
            follow_through = (float(last["c"]) - float(prev["c"])) / max(float(prev["spread"]), 1e-9)
            if abs(follow_through) < 0.2:
                signals.append("effort_no_result")
                score += -15 if float(prev["c"]) > float(prev["o"]) else 15

    # Pseudo Upthrust
    if is_up and wide_spread and high_vol and c_pos < 0.4:
        signals.append("pseudo_upthrust"); score -= 28

    payload = {
        "signals": signals, "trend_proxy": trend,
        "spread_ratio": round(s / max(avg_spread, 1e-9), 2),
        "vol_ratio": round(v / max(avg_vol, 1e-9), 2),
        "c_pos": round(c_pos, 3),
    }
    if score >= 20:
        return AnalyzerResult(CODE, "buy", min(85.0, 40 + score), WEIGHT_DEFAULT, payload)
    if score <= -20:
        return AnalyzerResult(CODE, "sell", min(85.0, 40 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class VolumeSpreadAnalysisAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
