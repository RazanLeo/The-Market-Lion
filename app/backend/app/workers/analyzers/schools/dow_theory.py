"""Dow Theory — primary, secondary, minor trend identification + volume confirmation + averages must confirm."""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "dow_theory"
WEIGHT_DEFAULT = 1.1


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 220 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]; v = df["v"].fillna(0)
    sma200 = c.rolling(200).mean()
    sma200_slope = (sma200.iloc[-1] - sma200.iloc[-50]) / sma200.iloc[-50]
    primary = "up" if sma200_slope > 0.005 else "down" if sma200_slope < -0.005 else "flat"

    sub = df.iloc[-50:]
    sec_high = float(sub["h"].max()); sec_low = float(sub["l"].min())
    sec_range = sec_high - sec_low
    last_close = float(c.iloc[-1])
    sec_retrace = (sec_high - last_close) / sec_range if sec_range > 0 else 0
    secondary = "uptrend_pullback" if primary == "up" and 0.33 <= sec_retrace <= 0.66 else \
                "downtrend_rally" if primary == "down" and 0.33 <= (1 - sec_retrace) <= 0.66 else "with_primary"

    up_bars = (c > c.shift()).iloc[-50:]
    up_vol = float(v.iloc[-50:][up_bars].sum())
    dn_vol = float(v.iloc[-50:][~up_bars].sum()) or 1
    vol_ratio = up_vol / dn_vol
    vol_confirms_up = vol_ratio > 1.15; vol_confirms_dn = vol_ratio < 0.87

    ema200 = c.ewm(span=200, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()
    avg_confirms_up = float(ema50.iloc[-1]) > float(ema200.iloc[-1]) and float(ema50.iloc[-1]) > float(ema50.iloc[-20])
    avg_confirms_dn = float(ema50.iloc[-1]) < float(ema200.iloc[-1]) and float(ema50.iloc[-1]) < float(ema50.iloc[-20])

    sub30 = df.iloc[-30:]
    body_pos = ((sub30["c"] - sub30["l"]) / (sub30["h"] - sub30["l"] + 1e-9))
    weighted_pos = (body_pos * v.iloc[-30:]).sum() / max(v.iloc[-30:].sum(), 1)
    phase = "accumulation" if weighted_pos > 0.55 else "distribution" if weighted_pos < 0.45 else "neutral"

    payload = {"primary": primary, "secondary": secondary,
               "sma200_slope_50bars_pct": round(float(sma200_slope) * 100, 3),
               "vol_up_dn_ratio": round(vol_ratio, 2),
               "vol_confirms_up": vol_confirms_up, "vol_confirms_dn": vol_confirms_dn,
               "averages_confirm_up": avg_confirms_up, "averages_confirm_dn": avg_confirms_dn,
               "phase": phase, "weighted_close_pos": round(float(weighted_pos), 3)}
    score = 0.0
    if primary == "up": score += 25
    if primary == "down": score -= 25
    if vol_confirms_up: score += 15
    if vol_confirms_dn: score -= 15
    if avg_confirms_up: score += 12
    if avg_confirms_dn: score -= 12
    if phase == "accumulation": score += 10
    if phase == "distribution": score -= 10
    if primary == "up" and secondary == "uptrend_pullback": score += 8
    if primary == "down" and secondary == "downtrend_rally": score -= 8

    if score >= 25:
        return AnalyzerResult(CODE, "buy", min(85.0, 45 + score * 0.8), WEIGHT_DEFAULT, payload)
    if score <= -25:
        return AnalyzerResult(CODE, "sell", min(85.0, 45 + abs(score) * 0.8), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class DowTheoryAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
