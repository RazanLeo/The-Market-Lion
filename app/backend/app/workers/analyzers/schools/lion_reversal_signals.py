"""Lion Reversal Signals — composite reversal detector across 4 axes.

Counts how many of these are TRUE:
  1. RSI divergence (regular bull/bear)
  2. Candlestick reversal pattern (Doji, Hammer, Shooting Star, Engulfing)
  3. Test of major S/R level (within 0.4×ATR of last 50-bar high/low)
  4. Volume climax (last 3-bar volume > 2× 50-bar avg)
≥2 of 4 in same direction = reversal signal.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_reversal_signals"
WEIGHT_DEFAULT = 1.05


def _rsi(c: pd.Series, p: int = 14) -> pd.Series:
    delta = c.diff()
    up = delta.where(delta > 0, 0).ewm(alpha=1/p, adjust=False).mean()
    dn = -delta.where(delta < 0, 0).ewm(alpha=1/p, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]; h = df["h"]; l = df["l"]; o = df["o"]
    rsi = _rsi(c)
    win = df.iloc[-30:]; rsi_w = rsi.iloc[-30:]
    p_high = int(win["c"].argmax()); p_low = int(win["c"].argmin())
    bull_div = bear_div = False
    if p_high > 5:
        e = int(win["c"].iloc[:p_high].argmax())
        if win["c"].iloc[p_high] > win["c"].iloc[e] and rsi_w.iloc[p_high] < rsi_w.iloc[e]:
            bear_div = True
    if p_low > 5:
        e = int(win["c"].iloc[:p_low].argmin())
        if win["c"].iloc[p_low] < win["c"].iloc[e] and rsi_w.iloc[p_low] > rsi_w.iloc[e]:
            bull_div = True
    last_o = float(o.iloc[-1]); last_h = float(h.iloc[-1])
    last_l = float(l.iloc[-1]); last_c = float(c.iloc[-1])
    rng = max(last_h - last_l, 1e-9)
    body = abs(last_c - last_o)
    upper_sh = last_h - max(last_c, last_o); lower_sh = min(last_c, last_o) - last_l
    doji = body / rng < 0.10
    hammer = body / rng < 0.30 and lower_sh / rng > 0.6 and upper_sh / rng < 0.15
    shooting_star = body / rng < 0.30 and upper_sh / rng > 0.6 and lower_sh / rng < 0.15
    pc = float(c.iloc[-2]); po = float(o.iloc[-2])
    bull_eng = pc < po and last_c > last_o and last_o <= pc and last_c >= po
    bear_eng = pc > po and last_c < last_o and last_o >= pc and last_c <= po
    bull_pattern = hammer or bull_eng
    bear_pattern = shooting_star or bear_eng
    h50 = float(h.iloc[-51:-1].max()); l50 = float(l.iloc[-51:-1].min())
    atr = float((h - l).rolling(14).mean().iloc[-1] or 1)
    near_res = abs(last_c - h50) < atr * 0.4
    near_sup = abs(last_c - l50) < atr * 0.4
    if "v" in df.columns:
        avg_v = float(df["v"].rolling(50).mean().iloc[-1] or 1)
        last_3v = float(df["v"].iloc[-3:].sum())
        vol_climax = last_3v > avg_v * 6
    else:
        vol_climax = False
    bull_score = sum([bull_div, bull_pattern or doji, near_sup, vol_climax])
    bear_score = sum([bear_div, bear_pattern or doji, near_res, vol_climax])
    payload = {"bull_div": bull_div, "bear_div": bear_div,
               "bull_pattern": bull_pattern, "bear_pattern": bear_pattern,
               "doji": doji, "near_resistance": near_res, "near_support": near_sup,
               "vol_climax": vol_climax,
               "bull_score": bull_score, "bear_score": bear_score}
    if bull_score >= 2 and bull_score > bear_score:
        return AnalyzerResult(CODE, "buy", min(85.0, 50 + bull_score * 10), WEIGHT_DEFAULT, payload)
    if bear_score >= 2 and bear_score > bull_score:
        return AnalyzerResult(CODE, "sell", min(85.0, 50 + bear_score * 10), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionReversalSignalsAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
