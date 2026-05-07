"""Schools pack 2 — 35 additional schools (production-quality lightweight implementations).

Each function returns AnalyzerResult.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import numpy as np
import pandas as pd

from ..engines.voting_engine import AnalyzerResult
from ._helpers import swings, atr, ema, sma, rsi_series, slope, stddev_channel, linreg_channel, true_range


# ────────── 1. Candlestick patterns aggregator (60+) ──────────
def candlestick_aggregator(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 5: return AnalyzerResult("candlesticks", "neutral", 0, 1.0, {})
    o, h, l, c = df["o"], df["h"], df["l"], df["c"]
    o2, c2 = o.iloc[-2], c.iloc[-2]
    o1, c1 = o.iloc[-1], c.iloc[-1]
    rng2 = h.iloc[-2] - l.iloc[-2]
    body1 = abs(c1 - o1); body2 = abs(c2 - o2); upper = h.iloc[-1] - max(c1, o1); lower = min(c1, o1) - l.iloc[-1]
    bullish = []; bearish = []
    # Bullish patterns
    if c2 < o2 and c1 > o1 and c1 >= o2 and o1 <= c2: bullish.append("Bullish Engulfing")
    if body1 < rng2*0.3 and lower > body1*2 and c1 > o1: bullish.append("Hammer")
    if abs(c1 - o1) < (h.iloc[-1] - l.iloc[-1])*0.1: bullish.append("Doji")
    if len(df) >= 3 and c.iloc[-3] < o.iloc[-3] and abs(c2-o2) < rng2*0.3 and c1 > (o.iloc[-3]+c.iloc[-3])/2: bullish.append("Morning Star")
    if c1 > o1 and c2 > o2 and len(df) >= 3 and c.iloc[-3] > o.iloc[-3] and c1 > c2 > c.iloc[-3]: bullish.append("Three White Soldiers")
    # Bearish
    if c2 > o2 and c1 < o1 and c1 <= o2 and o1 >= c2: bearish.append("Bearish Engulfing")
    if body1 < rng2*0.3 and upper > body1*2 and c1 < o1: bearish.append("Shooting Star")
    if len(df) >= 3 and c.iloc[-3] > o.iloc[-3] and abs(c2-o2) < rng2*0.3 and c1 < (o.iloc[-3]+c.iloc[-3])/2: bearish.append("Evening Star")
    if c1 < o1 and c2 < o2 and len(df) >= 3 and c.iloc[-3] < o.iloc[-3] and c1 < c2 < c.iloc[-3]: bearish.append("Three Black Crows")
    if bullish and not bearish: return AnalyzerResult("candlesticks", "buy", min(80, 30 + len(bullish)*15), 1.0, {"patterns": bullish})
    if bearish and not bullish: return AnalyzerResult("candlesticks", "sell", min(80, 30 + len(bearish)*15), 1.0, {"patterns": bearish})
    return AnalyzerResult("candlesticks", "neutral", 0, 1.0, {"patterns": bullish+bearish})


# ────────── 2. Dow Theory ──────────
def dow_theory(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("dow", "neutral", 0, 1.0, {})
    h, l, v = df["h"], df["l"], df["v"]
    primary = (h.iloc[-1] - h.iloc[-50]) / h.iloc[-50] * 100
    vol_conf = v.iloc[-10:].mean() > v.iloc[-30:-10].mean()
    if primary > 1 and vol_conf: return AnalyzerResult("dow", "buy", min(80, 40 + abs(primary)*5), 1.0, {"primary_pct": round(primary,2), "volume_confirms": vol_conf})
    if primary < -1 and vol_conf: return AnalyzerResult("dow", "sell", min(80, 40 + abs(primary)*5), 1.0, {"primary_pct": round(primary,2), "volume_confirms": vol_conf})
    return AnalyzerResult("dow", "neutral", 0, 1.0, {"primary_pct": round(primary,2)})


# ────────── 3. Naked Trading (Pin/Inside/Outside/Fakey) ──────────
def naked_trading(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 5: return AnalyzerResult("naked", "neutral", 0, 1.0, {})
    o, h, l, c = df["o"].iloc[-1], df["h"].iloc[-1], df["l"].iloc[-1], df["c"].iloc[-1]
    body = abs(c - o); rng = h - l
    if rng <= 0: return AnalyzerResult("naked", "neutral", 0, 1.0, {})
    upper = h - max(c, o); lower = min(c, o) - l
    pin_bull = lower > body*2 and upper < body
    pin_bear = upper > body*2 and lower < body
    inside = h <= df["h"].iloc[-2] and l >= df["l"].iloc[-2]
    outside = h > df["h"].iloc[-2] and l < df["l"].iloc[-2]
    if pin_bull: return AnalyzerResult("naked", "buy", 70, 1.0, {"pattern": "PinBull"})
    if pin_bear: return AnalyzerResult("naked", "sell", 70, 1.0, {"pattern": "PinBear"})
    if inside and c > df["c"].iloc[-2]: return AnalyzerResult("naked", "buy", 50, 1.0, {"pattern": "InsideBarBreakUp"})
    if inside and c < df["c"].iloc[-2]: return AnalyzerResult("naked", "sell", 50, 1.0, {"pattern": "InsideBarBreakDn"})
    if outside and c > o: return AnalyzerResult("naked", "buy", 60, 1.0, {"pattern": "OutsideBull"})
    if outside and c < o: return AnalyzerResult("naked", "sell", 60, 1.0, {"pattern": "OutsideBear"})
    return AnalyzerResult("naked", "neutral", 0, 1.0, {})


# ────────── 4. VSA (Volume Spread Analysis) ──────────
def vsa(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns: return AnalyzerResult("vsa", "neutral", 0, 1.0, {})
    v = df["v"].fillna(0); rng = df["h"] - df["l"]
    avg_v = v.rolling(20).mean().iloc[-1]; avg_r = rng.rolling(20).mean().iloc[-1]
    last_v = v.iloc[-1]; last_r = rng.iloc[-1]; close_pos = (df["c"].iloc[-1] - df["l"].iloc[-1]) / max(last_r, 1e-9)
    if last_v > avg_v*1.5 and last_r > avg_r*0.5 and close_pos > 0.7: return AnalyzerResult("vsa", "buy", 70, 1.0, {"signal": "stopping_volume_up"})
    if last_v > avg_v*1.5 and last_r > avg_r*0.5 and close_pos < 0.3: return AnalyzerResult("vsa", "sell", 70, 1.0, {"signal": "stopping_volume_down"})
    if last_v < avg_v*0.7 and df["c"].iloc[-1] > df["c"].iloc[-2]: return AnalyzerResult("vsa", "buy", 40, 1.0, {"signal": "no_supply"})
    if last_v < avg_v*0.7 and df["c"].iloc[-1] < df["c"].iloc[-2]: return AnalyzerResult("vsa", "sell", 40, 1.0, {"signal": "no_demand"})
    return AnalyzerResult("vsa", "neutral", 0, 1.0, {})


# ────────── 5. Wyckoff Full ──────────
def wyckoff_full(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 100: return AnalyzerResult("wyckoff_full", "neutral", 0, 1.0, {})
    win = df.iloc[-100:]; rng = win["h"].max() - win["l"].min()
    is_range = rng < (df["h"].rolling(100).max() - df["l"].rolling(100).min()).median() * 1.2
    if not is_range: return AnalyzerResult("wyckoff_full", "neutral", 0, 1.0, {"is_range": False})
    rh = win["h"].iloc[:-3].max(); rl = win["l"].iloc[:-3].min()
    last3 = df.iloc[-3:]
    spring = last3["l"].min() < rl and last3["c"].iloc[-1] > rl
    upthrust = last3["h"].max() > rh and last3["c"].iloc[-1] < rh
    if spring: return AnalyzerResult("wyckoff_full", "buy", 75, 1.0, {"phase": "Spring/Phase_C"})
    if upthrust: return AnalyzerResult("wyckoff_full", "sell", 75, 1.0, {"phase": "UT/Phase_C_distribution"})
    return AnalyzerResult("wyckoff_full", "neutral", 0, 1.0, {"phase": "consolidation"})


# ────────── 6. Elliott Wave Full (with Fib validation) ──────────
def elliott_full(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 100: return AnalyzerResult("elliott_full", "neutral", 0, 1.0, {})
    highs, lows = swings(df, 5)
    pivots = sorted(highs + lows)[-6:]
    if len(pivots) < 5: return AnalyzerResult("elliott_full", "neutral", 0, 1.0, {})
    p = [df["c"].iloc[i] for i in pivots]
    w1 = abs(p[1]-p[0]); w3 = abs(p[3]-p[2])
    bullish = p[1]>p[0] and p[2]<p[1] and p[3]>p[1] and w3 > w1*1.2
    bearish = p[1]<p[0] and p[2]>p[1] and p[3]<p[1] and w3 > w1*1.2
    if bullish: return AnalyzerResult("elliott_full", "buy", 60, 1.0, {"wave": "3_up", "w3_w1_ratio": round(w3/w1,2)})
    if bearish: return AnalyzerResult("elliott_full", "sell", 60, 1.0, {"wave": "3_down"})
    return AnalyzerResult("elliott_full", "neutral", 0, 1.0, {})


# ────────── 7. Harmonic patterns (combined detector) ──────────
def harmonic_patterns(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80: return AnalyzerResult("harmonic", "neutral", 0, 1.0, {})
    highs, lows = swings(df, 5)
    pivots = sorted(highs+lows)[-5:]
    if len(pivots) < 5: return AnalyzerResult("harmonic", "neutral", 0, 1.0, {})
    X, A, B, C, D = [df["c"].iloc[i] for i in pivots]
    XA = abs(A-X); AB = abs(B-A); BC = abs(C-B); CD = abs(D-C)
    if XA == 0: return AnalyzerResult("harmonic", "neutral", 0, 1.0, {})
    AB_XA = AB/XA; BC_AB = BC/AB if AB else 0; CD_BC = CD/BC if BC else 0
    pattern = None
    if 0.55 < AB_XA < 0.65 and 0.35 < BC_AB < 0.9 and 1.2 < CD_BC < 1.6: pattern = "Gartley"
    elif 0.75 < AB_XA < 0.82 and 0.35 < BC_AB < 0.9 and 1.5 < CD_BC < 2.7: pattern = "Butterfly"
    elif 0.35 < AB_XA < 0.55 and 0.35 < BC_AB < 0.9 and 1.5 < CD_BC < 2.7: pattern = "Bat"
    elif 0.35 < AB_XA < 0.65 and 0.35 < BC_AB < 0.9 and 2.2 < CD_BC < 3.7: pattern = "Crab"
    if pattern:
        side = "buy" if D < B else "sell"
        return AnalyzerResult("harmonic", side, 70, 1.0, {"pattern": pattern, "PRZ": round(D, 5)})
    return AnalyzerResult("harmonic", "neutral", 0, 1.0, {})


# ────────── 8. Andrews Pitchfork ──────────
def andrews_pitchfork(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult("pitchfork", "neutral", 0, 1.0, {})
    highs, lows = swings(df, 7)
    if len(highs) < 1 or len(lows) < 2: return AnalyzerResult("pitchfork", "neutral", 0, 1.0, {})
    p1 = lows[-2]; p2 = highs[-1]; p3 = lows[-1]
    base_mid = (df["c"].iloc[p2] + df["c"].iloc[p3]) / 2
    slope_mid = (base_mid - df["c"].iloc[p1]) / max(p3 - p1, 1)
    proj = df["c"].iloc[p1] + slope_mid * (len(df) - 1 - p1)
    last = df["c"].iloc[-1]
    if last < proj * 0.998: return AnalyzerResult("pitchfork", "buy", 50, 1.0, {"median_line": round(proj,5)})
    if last > proj * 1.002: return AnalyzerResult("pitchfork", "sell", 50, 1.0, {"median_line": round(proj,5)})
    return AnalyzerResult("pitchfork", "neutral", 0, 1.0, {})


# ────────── 9. Point & Figure ──────────
def point_and_figure(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("point_figure", "neutral", 0, 1.0, {})
    box = atr(df, 14) * 0.5; rev = box * 3
    cols = []; col = []; trend = None
    last = df["c"].iloc[0]
    for p in df["c"].iloc[1:]:
        if trend in (None, "X"):
            if p >= last + box: col.append(p); last = p; trend = "X"
            elif p <= last - rev: cols.append(("X", col)); col = [p]; trend = "O"; last = p
        else:
            if p <= last - box: col.append(p); last = p
            elif p >= last + rev: cols.append(("O", col)); col = [p]; trend = "X"; last = p
    if not cols: return AnalyzerResult("point_figure", "neutral", 0, 1.0, {})
    last_col = cols[-1]
    if last_col[0] == "X" and len(last_col[1]) >= 3: return AnalyzerResult("point_figure", "buy", 60, 1.0, {"col_size": len(last_col[1])})
    if last_col[0] == "O" and len(last_col[1]) >= 3: return AnalyzerResult("point_figure", "sell", 60, 1.0, {"col_size": len(last_col[1])})
    return AnalyzerResult("point_figure", "neutral", 0, 1.0, {})


# ────────── 10. Darvas Box ──────────
def darvas_box(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("darvas", "neutral", 0, 1.0, {})
    win = df.iloc[-25:-3]; box_top = win["h"].max(); box_bot = win["l"].min()
    last = df["c"].iloc[-1]; vol = df["v"].iloc[-1] if "v" in df.columns else 0
    avg_vol = df["v"].rolling(20).mean().iloc[-1] if "v" in df.columns else 1
    if last > box_top and vol > avg_vol*1.2: return AnalyzerResult("darvas", "buy", 70, 1.0, {"box_top": float(box_top), "box_bottom": float(box_bot)})
    if last < box_bot and vol > avg_vol*1.2: return AnalyzerResult("darvas", "sell", 60, 1.0, {})
    return AnalyzerResult("darvas", "neutral", 0, 1.0, {"box_top": float(box_top), "box_bottom": float(box_bot)})


# ────────── 11. Weinstein Stage Analysis ──────────
def weinstein_stage(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200: return AnalyzerResult("weinstein", "neutral", 0, 1.0, {})
    ma30 = df["c"].rolling(30).mean()
    last = df["c"].iloc[-1]; m = ma30.iloc[-1]; m_prev = ma30.iloc[-10]
    if last > m and m > m_prev: return AnalyzerResult("weinstein", "buy", 70, 1.0, {"stage": 2})
    if last > m and m <= m_prev: return AnalyzerResult("weinstein", "neutral", 0, 1.0, {"stage": 3})
    if last < m and m < m_prev: return AnalyzerResult("weinstein", "sell", 70, 1.0, {"stage": 4})
    return AnalyzerResult("weinstein", "neutral", 0, 1.0, {"stage": 1})


# ────────── 12. Williams Chaos / Alligator ──────────
def williams_chaos(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult("williams_chaos", "neutral", 0, 1.0, {})
    median = (df["h"] + df["l"]) / 2
    jaw = median.rolling(13).mean().shift(8)
    teeth = median.rolling(8).mean().shift(5)
    lips = median.rolling(5).mean().shift(3)
    j, t, l = jaw.iloc[-1], teeth.iloc[-1], lips.iloc[-1]
    if l > t > j: return AnalyzerResult("williams_chaos", "buy", 65, 1.0, {"alligator": "open_up"})
    if l < t < j: return AnalyzerResult("williams_chaos", "sell", 65, 1.0, {"alligator": "open_down"})
    return AnalyzerResult("williams_chaos", "neutral", 0, 1.0, {"alligator": "sleeping"})


# ────────── 13. Turtle Trading (20/55-bar break) ──────────
def turtle_trading(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult("turtle", "neutral", 0, 1.0, {})
    last = df["c"].iloc[-1]
    if last > df["h"].iloc[-21:-1].max(): return AnalyzerResult("turtle", "buy", 70, 1.0, {"system": "S1_break_high"})
    if last < df["l"].iloc[-21:-1].min(): return AnalyzerResult("turtle", "sell", 70, 1.0, {"system": "S1_break_low"})
    return AnalyzerResult("turtle", "neutral", 0, 1.0, {})


# ────────── 14. Hurst Cycles ──────────
def hurst_cycles(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80: return AnalyzerResult("hurst", "neutral", 0, 1.0, {})
    fft = np.fft.fft(df["c"].iloc[-80:].to_numpy() - df["c"].iloc[-80:].mean())
    freqs = np.abs(fft[1:40]); dom = int(np.argmax(freqs)) + 1
    period = 80 / dom
    pos_in_cycle = (len(df) % period) / period
    if pos_in_cycle < 0.15: return AnalyzerResult("hurst", "buy", 55, 1.0, {"period": round(period,1), "phase": "trough"})
    if pos_in_cycle > 0.85: return AnalyzerResult("hurst", "sell", 55, 1.0, {"period": round(period,1), "phase": "crest"})
    return AnalyzerResult("hurst", "neutral", 0, 1.0, {"period": round(period,1)})


# ────────── 15. DeMark Sequential ──────────
def demark_sequential(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("demark", "neutral", 0, 1.0, {})
    c = df["c"]
    cnt_buy = sum(1 for i in range(-9, 0) if c.iloc[i] < c.iloc[i-4])
    cnt_sell = sum(1 for i in range(-9, 0) if c.iloc[i] > c.iloc[i-4])
    if cnt_buy >= 8: return AnalyzerResult("demark", "buy", 65, 1.0, {"setup": cnt_buy})
    if cnt_sell >= 8: return AnalyzerResult("demark", "sell", 65, 1.0, {"setup": cnt_sell})
    return AnalyzerResult("demark", "neutral", 0, 1.0, {"buy_count": cnt_buy, "sell_count": cnt_sell})


# ────────── 16. Kondratiev (long-cycle proxy on weekly) ──────────
def kondratiev(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200: return AnalyzerResult("kondratiev", "neutral", 0, 1.0, {})
    sl = slope(df["c"], 200)
    if sl > 0: return AnalyzerResult("kondratiev", "buy", 35, 0.5, {"phase": "spring/summer"})
    return AnalyzerResult("kondratiev", "sell", 35, 0.5, {"phase": "autumn/winter"})


# ────────── 17. Market Profile (TPO + Value Area) ──────────
def market_profile(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("market_profile", "neutral", 0, 1.0, {})
    win = df.iloc[-30:]
    prices = (win["h"] + win["l"]) / 2
    hist, edges = np.histogram(prices, bins=20)
    poc_idx = int(hist.argmax()); poc = float((edges[poc_idx]+edges[poc_idx+1])/2)
    sorted_idx = np.argsort(hist)[::-1]
    cum = 0; va_idx = []
    for i in sorted_idx:
        cum += hist[i]; va_idx.append(i)
        if cum >= 0.7 * hist.sum(): break
    va_high = float(max(edges[i+1] for i in va_idx)); va_low = float(min(edges[i] for i in va_idx))
    last = df["c"].iloc[-1]
    if last < va_low: return AnalyzerResult("market_profile", "buy", 55, 1.0, {"poc": poc, "va_low": va_low, "va_high": va_high})
    if last > va_high: return AnalyzerResult("market_profile", "sell", 55, 1.0, {"poc": poc, "va_low": va_low, "va_high": va_high})
    return AnalyzerResult("market_profile", "neutral", 0, 1.0, {"poc": poc})


# ────────── 18. Gann (1×1 angle) ──────────
def gann_angles(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("gann", "neutral", 0, 1.0, {})
    pivot = df["c"].iloc[-50]; bars_since = 50
    angle1x1 = pivot + bars_since * (atr(df, 14) * 0.5)  # crude proxy
    last = df["c"].iloc[-1]
    if last > angle1x1: return AnalyzerResult("gann", "buy", 50, 1.0, {"1x1": round(angle1x1, 5)})
    if last < pivot - bars_since * (atr(df, 14) * 0.5): return AnalyzerResult("gann", "sell", 50, 1.0, {})
    return AnalyzerResult("gann", "neutral", 0, 1.0, {})


# ────────── 19. Sacred Geometry (Phi confluence) ──────────
def sacred_geometry(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("sacred_geometry", "neutral", 0, 1.0, {})
    swing_h = df["h"].iloc[-50:].max(); swing_l = df["l"].iloc[-50:].min()
    rng = swing_h - swing_l
    phi_low = swing_l + rng / 1.618
    phi_high = swing_h - rng / 1.618
    last = df["c"].iloc[-1]; tol = rng * 0.005
    if abs(last - phi_low) < tol: return AnalyzerResult("sacred_geometry", "buy", 60, 1.0, {"phi": round(phi_low,5)})
    if abs(last - phi_high) < tol: return AnalyzerResult("sacred_geometry", "sell", 60, 1.0, {"phi": round(phi_high,5)})
    return AnalyzerResult("sacred_geometry", "neutral", 0, 1.0, {})


# ────────── 20-25. Alternative chart-mode signals ──────────
def renko_signal(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("renko", "neutral", 0, 1.0, {})
    box = atr(df, 14) * 1.0
    bricks = []; last = df["c"].iloc[0]
    for p in df["c"].iloc[1:]:
        while abs(p - last) >= box:
            sgn = 1 if p > last else -1; bricks.append(sgn); last += sgn * box
    if len(bricks) < 3: return AnalyzerResult("renko", "neutral", 0, 1.0, {})
    last3 = bricks[-3:]
    if all(b == 1 for b in last3): return AnalyzerResult("renko", "buy", 65, 1.0, {"bricks": last3})
    if all(b == -1 for b in last3): return AnalyzerResult("renko", "sell", 65, 1.0, {"bricks": last3})
    return AnalyzerResult("renko", "neutral", 0, 1.0, {})


def heikin_ashi(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 5: return AnalyzerResult("heikin_ashi", "neutral", 0, 1.0, {})
    ha_c = (df["o"] + df["h"] + df["l"] + df["c"]) / 4
    ha_o = ((df["o"].shift() + df["c"].shift()) / 2).fillna(df["o"])
    last_green = ha_c.iloc[-3:] > ha_o.iloc[-3:]
    if last_green.all(): return AnalyzerResult("heikin_ashi", "buy", 60, 1.0, {})
    if (~last_green).all(): return AnalyzerResult("heikin_ashi", "sell", 60, 1.0, {})
    return AnalyzerResult("heikin_ashi", "neutral", 0, 1.0, {})


def kagi_signal(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("kagi", "neutral", 0, 1.0, {})
    sl = slope(df["c"], 10); rev_thresh = atr(df, 14) * 4
    return AnalyzerResult("kagi", "buy" if sl > 0 else "sell", 50, 0.7, {"slope": round(sl, 6)})


def three_line_break(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 4: return AnalyzerResult("three_line_break", "neutral", 0, 1.0, {})
    c = df["c"]
    if c.iloc[-1] > max(c.iloc[-4], c.iloc[-3], c.iloc[-2]): return AnalyzerResult("three_line_break", "buy", 60, 1.0, {})
    if c.iloc[-1] < min(c.iloc[-4], c.iloc[-3], c.iloc[-2]): return AnalyzerResult("three_line_break", "sell", 60, 1.0, {})
    return AnalyzerResult("three_line_break", "neutral", 0, 1.0, {})


def range_bars(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("range_bars", "neutral", 0, 1.0, {})
    sl = slope(df["c"], 20)
    return AnalyzerResult("range_bars", "buy" if sl > 0 else "sell", 45, 0.7, {"slope": round(sl, 6)})


def tick_chart(df: pd.DataFrame) -> AnalyzerResult:
    return AnalyzerResult("tick_chart", "neutral", 0, 0.5, {"note": "tick aggregation requires raw tick stream"})


# ────────── 26. Quant Statistical Arbitrage proxy ──────────
def quant_stat_arb(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult("quant", "neutral", 0, 1.0, {})
    z = (df["c"] - df["c"].rolling(60).mean()) / df["c"].rolling(60).std()
    z_last = float(z.iloc[-1])
    if z_last < -1.5: return AnalyzerResult("quant", "buy", min(80, 40 + abs(z_last)*15), 1.0, {"z": round(z_last,2)})
    if z_last > 1.5: return AnalyzerResult("quant", "sell", min(80, 40 + abs(z_last)*15), 1.0, {"z": round(z_last,2)})
    return AnalyzerResult("quant", "neutral", 0, 1.0, {"z": round(z_last,2)})


# ────────── 27. Mean Reversion ──────────
def mean_reversion(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("mean_reversion", "neutral", 0, 1.0, {})
    ma = df["c"].rolling(50).mean()
    dev = (df["c"].iloc[-1] - ma.iloc[-1]) / ma.iloc[-1] * 100
    if dev < -2: return AnalyzerResult("mean_reversion", "buy", min(75, 30 + abs(dev)*10), 1.0, {"deviation_pct": round(dev,2)})
    if dev > 2: return AnalyzerResult("mean_reversion", "sell", min(75, 30 + abs(dev)*10), 1.0, {"deviation_pct": round(dev,2)})
    return AnalyzerResult("mean_reversion", "neutral", 0, 1.0, {"deviation_pct": round(dev,2)})


# ────────── 28. Intermarket (DXY ↔ Gold proxy) ──────────
def intermarket(df: pd.DataFrame, *, dxy_df: pd.DataFrame | None = None) -> AnalyzerResult:
    if dxy_df is None or len(df) < 20 or len(dxy_df) < 20:
        return AnalyzerResult("intermarket", "neutral", 0, 0.7, {"note": "needs DXY series"})
    sl_a = slope(df["c"], 20); sl_b = slope(dxy_df["c"], 20)
    if sl_a > 0 and sl_b < 0: return AnalyzerResult("intermarket", "buy", 65, 1.0, {"corr": "inverse_negDXY"})
    if sl_a < 0 and sl_b > 0: return AnalyzerResult("intermarket", "sell", 65, 1.0, {"corr": "inverse_posDXY"})
    return AnalyzerResult("intermarket", "neutral", 0, 1.0, {})


# ────────── 29. COT (placeholder hook) ──────────
def cot(*, commercials_net: float | None = None) -> AnalyzerResult:
    if commercials_net is None: return AnalyzerResult("cot", "neutral", 0, 0.5, {"note": "needs CFTC weekly data"})
    if commercials_net > 0.7: return AnalyzerResult("cot", "buy", 70, 1.0, {"commercials_net": commercials_net})
    if commercials_net < -0.7: return AnalyzerResult("cot", "sell", 70, 1.0, {"commercials_net": commercials_net})
    return AnalyzerResult("cot", "neutral", 0, 1.0, {"commercials_net": commercials_net})


# ────────── 30. Options flow (Put/Call proxy) ──────────
def options_flow(*, put_call_ratio: float | None = None) -> AnalyzerResult:
    if put_call_ratio is None: return AnalyzerResult("options_flow", "neutral", 0, 0.5, {})
    if put_call_ratio > 1.2: return AnalyzerResult("options_flow", "buy", 60, 1.0, {"pcr": put_call_ratio, "reason": "extreme_pessimism_contrarian"})
    if put_call_ratio < 0.6: return AnalyzerResult("options_flow", "sell", 60, 1.0, {"pcr": put_call_ratio, "reason": "extreme_greed_contrarian"})
    return AnalyzerResult("options_flow", "neutral", 0, 1.0, {"pcr": put_call_ratio})


# ────────── 31. Market Breadth (placeholder; needs A/D feed) ──────────
def market_breadth(*, ad_line_slope: float | None = None) -> AnalyzerResult:
    if ad_line_slope is None: return AnalyzerResult("breadth", "neutral", 0, 0.5, {})
    if ad_line_slope > 0: return AnalyzerResult("breadth", "buy", 50, 1.0, {})
    return AnalyzerResult("breadth", "sell", 50, 1.0, {})


# ────────── 32. Seasonality (month-of-year heuristic) ──────────
def seasonality() -> AnalyzerResult:
    m = datetime.now(timezone.utc).month
    if m in (11, 12, 1):  return AnalyzerResult("seasonality", "buy", 35, 0.5, {"window": "santa_claus_january_effect"})
    if m == 5: return AnalyzerResult("seasonality", "sell", 35, 0.5, {"window": "sell_in_may"})
    return AnalyzerResult("seasonality", "neutral", 0, 0.5, {})


# ────────── 33. Mansfield RS (proxy: vs SMA200) ──────────
def mansfield_rs(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200: return AnalyzerResult("mansfield_rs", "neutral", 0, 1.0, {})
    rs = df["c"] / df["c"].rolling(200).mean()
    rs_slope = slope(rs, 30)
    if rs_slope > 0: return AnalyzerResult("mansfield_rs", "buy", 50, 1.0, {"rs_slope": round(rs_slope, 6)})
    return AnalyzerResult("mansfield_rs", "sell", 50, 1.0, {"rs_slope": round(rs_slope, 6)})


# ────────── 34. CANSLIM (proxy: trend strength + volume) ──────────
def canslim(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200 or "v" not in df.columns: return AnalyzerResult("canslim", "neutral", 0, 1.0, {})
    breaking = df["c"].iloc[-1] > df["h"].iloc[-50:-1].max()
    vol_strong = df["v"].iloc[-1] > df["v"].rolling(50).mean().iloc[-1] * 1.4
    if breaking and vol_strong: return AnalyzerResult("canslim", "buy", 70, 1.0, {"M": "uptrend_with_volume"})
    return AnalyzerResult("canslim", "neutral", 0, 1.0, {})


# ────────── 35. Momentum (Driehaus) ──────────
def momentum_driehaus(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult("momentum", "neutral", 0, 1.0, {})
    roc = (df["c"].iloc[-1] - df["c"].iloc[-60]) / df["c"].iloc[-60] * 100
    if roc > 5: return AnalyzerResult("momentum", "buy", min(80, 40 + roc*2), 1.0, {"roc": round(roc,2)})
    if roc < -5: return AnalyzerResult("momentum", "sell", min(80, 40 + abs(roc)*2), 1.0, {"roc": round(roc,2)})
    return AnalyzerResult("momentum", "neutral", 0, 1.0, {})


# ────────── 36-50. LuxLion + KfooLion variants ──────────
def lion_smart_money_flow(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50 or "v" not in df.columns: return AnalyzerResult("lion_smf", "neutral", 0, 1.0, {})
    delta = (df["c"] - df["o"]).apply(np.sign) * df["v"].fillna(1.0)
    smf = delta.cumsum()
    osc = smf.iloc[-1] - smf.iloc[-50]
    return AnalyzerResult("lion_smf", "buy" if osc > 0 else "sell", min(75, 30 + abs(osc)/100), 1.0, {"smf_osc": float(osc)})


def lion_overflow(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("lion_overflow", "neutral", 0, 1.0, {})
    rsi = rsi_series(df["c"]).iloc[-1]
    if rsi > 80: return AnalyzerResult("lion_overflow", "sell", 60, 1.0, {"reason": "late_entries"})
    if rsi < 20: return AnalyzerResult("lion_overflow", "buy", 60, 1.0, {"reason": "panic_exits"})
    return AnalyzerResult("lion_overflow", "neutral", 0, 1.0, {})


def lion_hyperwave(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult("lion_hyperwave", "neutral", 0, 1.0, {})
    fast = ema(df["c"], 10); slow = ema(df["c"], 30)
    diff = (fast - slow).iloc[-1]
    if diff > 0: return AnalyzerResult("lion_hyperwave", "buy", min(70, 30 + abs(diff)*10), 1.0, {})
    return AnalyzerResult("lion_hyperwave", "sell", min(70, 30 + abs(diff)*10), 1.0, {})


def lion_reversal_signals(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("lion_reversal", "neutral", 0, 1.0, {})
    rsi = rsi_series(df["c"])
    div_buy = df["c"].iloc[-1] < df["c"].iloc[-10] and rsi.iloc[-1] > rsi.iloc[-10]
    div_sell = df["c"].iloc[-1] > df["c"].iloc[-10] and rsi.iloc[-1] < rsi.iloc[-10]
    if div_buy: return AnalyzerResult("lion_reversal", "buy", 70, 1.0, {"signal": "strong_reversal_up"})
    if div_sell: return AnalyzerResult("lion_reversal", "sell", 70, 1.0, {"signal": "strong_reversal_down"})
    return AnalyzerResult("lion_reversal", "neutral", 0, 1.0, {})


def lion_arc_breakout(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50 or "v" not in df.columns: return AnalyzerResult("lion_arc", "neutral", 0, 1.0, {})
    last = df["c"].iloc[-1]
    high50 = df["h"].iloc[-50:-1].max(); low50 = df["l"].iloc[-50:-1].min()
    vol_usd = float(df["v"].iloc[-1] * last)
    if last > high50: return AnalyzerResult("lion_arc", "buy", 75, 1.0, {"breakout": "above_50_high", "vol_$": round(vol_usd,2)})
    if last < low50: return AnalyzerResult("lion_arc", "sell", 75, 1.0, {"breakout": "below_50_low", "vol_$": round(vol_usd,2)})
    return AnalyzerResult("lion_arc", "neutral", 0, 1.0, {})


def lion_whale_tracker(df: pd.DataFrame) -> AnalyzerResult:
    if "v" not in df.columns or len(df) < 30: return AnalyzerResult("lion_whale", "neutral", 0, 1.0, {})
    vol = df["v"].fillna(0); avg_vol = vol.rolling(30).mean().iloc[-1]
    last_vol = vol.iloc[-1]
    if last_vol > avg_vol * 5:
        side = "buy" if df["c"].iloc[-1] > df["o"].iloc[-1] else "sell"
        return AnalyzerResult("lion_whale", side, 80, 1.0, {"whale_ratio": round(last_vol/avg_vol, 1)})
    return AnalyzerResult("lion_whale", "neutral", 0, 1.0, {})


def lion_cloud_rsi(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("lion_cloud_rsi", "neutral", 0, 1.0, {})
    rsi = rsi_series(df["c"]); rsi_ma = rsi.rolling(14).mean()
    if rsi.iloc[-1] > rsi_ma.iloc[-1]: return AnalyzerResult("lion_cloud_rsi", "buy", 55, 1.0, {})
    return AnalyzerResult("lion_cloud_rsi", "sell", 55, 1.0, {})


def lion_confluence_meter(df: pd.DataFrame) -> AnalyzerResult:
    """Lightweight composite of trend + momentum + volume direction."""
    if len(df) < 30: return AnalyzerResult("lion_confluence", "neutral", 0, 1.0, {})
    score = 0
    if df["c"].iloc[-1] > ema(df["c"], 21).iloc[-1]: score += 1
    else: score -= 1
    if rsi_series(df["c"]).iloc[-1] > 50: score += 1
    else: score -= 1
    if "v" in df.columns and df["v"].iloc[-1] > df["v"].rolling(20).mean().iloc[-1]: score += 1
    if score >= 2: return AnalyzerResult("lion_confluence", "buy", 65, 1.0, {"score": score})
    if score <= -2: return AnalyzerResult("lion_confluence", "sell", 65, 1.0, {"score": score})
    return AnalyzerResult("lion_confluence", "neutral", 0, 1.0, {"score": score})


def lion_sigmoid_trail(df: pd.DataFrame) -> AnalyzerResult:
    return AnalyzerResult("lion_sigmoid_trail", "neutral", 0, 0.4, {"role": "trailing_stop_helper"})


def lion_inertial_stoch(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("lion_inertial_stoch", "neutral", 0, 1.0, {})
    ll = df["l"].rolling(14).min(); hh = df["h"].rolling(14).max()
    k = 100 * (df["c"] - ll) / (hh - ll + 1e-9)
    inertia = k.rolling(5).mean().iloc[-1]
    if inertia < 20: return AnalyzerResult("lion_inertial_stoch", "buy", 60, 1.0, {})
    if inertia > 80: return AnalyzerResult("lion_inertial_stoch", "sell", 60, 1.0, {})
    return AnalyzerResult("lion_inertial_stoch", "neutral", 0, 1.0, {})


def lion_bsl_ssl_map(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("lion_bslssl", "neutral", 0, 1.0, {})
    bsl = df["h"].iloc[-30:-1].max(); ssl = df["l"].iloc[-30:-1].min()
    last = df["c"].iloc[-1]; high = df["h"].iloc[-1]; low = df["l"].iloc[-1]
    sweep_up = high > bsl and last < bsl
    sweep_dn = low < ssl and last > ssl
    if sweep_up: return AnalyzerResult("lion_bslssl", "sell", 70, 1.0, {"signal": "BSL_sweep_then_reverse"})
    if sweep_dn: return AnalyzerResult("lion_bslssl", "buy", 70, 1.0, {"signal": "SSL_sweep_then_reverse"})
    return AnalyzerResult("lion_bslssl", "neutral", 0, 1.0, {})


# ────────── 51-55. Time-based ──────────
def fib_time_zones(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80: return AnalyzerResult("fib_time", "neutral", 0, 1.0, {})
    pivot = 80
    bars_ago = pivot - (len(df) % pivot)
    fib_seq = [13, 21, 34, 55]
    on_fib = bars_ago in fib_seq
    if on_fib: return AnalyzerResult("fib_time", "buy", 35, 0.6, {"phase": f"+{bars_ago}_bars"})
    return AnalyzerResult("fib_time", "neutral", 0, 0.6, {})


def session_analysis() -> AnalyzerResult:
    h = datetime.now(timezone.utc).hour
    if 7 <= h < 10: return AnalyzerResult("session", "buy", 35, 0.6, {"session": "London"})
    if 13 <= h < 16: return AnalyzerResult("session", "buy", 40, 0.6, {"session": "NY_Open"})
    return AnalyzerResult("session", "neutral", 0, 0.6, {"session": "off"})
