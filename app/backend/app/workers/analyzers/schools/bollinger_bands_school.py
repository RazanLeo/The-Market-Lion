"""Bollinger Bands School — BB(20,2) + Squeeze (vs Keltner Channels) + walking the bands + %B + bandwidth.

Squeeze rule (John Carter / TTM): BB lies INSIDE the Keltner Channels (i.e., upper BB < upper KC AND
lower BB > lower KC). When the squeeze releases, expect a strong directional move.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "bollinger_bands_school"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    c = df["c"]
    sma20 = c.rolling(20).mean()
    sd20 = c.rolling(20).std()
    upper = sma20 + 2 * sd20
    lower = sma20 - 2 * sd20
    pct_b = (c - lower) / (upper - lower).replace(0, 1e-9)
    bandwidth = (upper - lower) / sma20

    # Keltner Channels (typical: EMA20 ± 1.5 × ATR(20))
    tr = pd.concat([df["h"] - df["l"], (df["h"] - c.shift()).abs(), (df["l"] - c.shift()).abs()], axis=1).max(axis=1)
    atr20 = tr.rolling(20).mean()
    kc_upper = c.ewm(span=20, adjust=False).mean() + 1.5 * atr20
    kc_lower = c.ewm(span=20, adjust=False).mean() - 1.5 * atr20

    bb_u = float(upper.iloc[-1]); bb_l = float(lower.iloc[-1])
    kc_u = float(kc_upper.iloc[-1]); kc_l = float(kc_lower.iloc[-1])
    pb = float(pct_b.iloc[-1])
    bw = float(bandwidth.iloc[-1])
    bw_avg = float(bandwidth.rolling(50).mean().iloc[-1] or bw)
    last_c = float(c.iloc[-1])

    in_squeeze = bb_u < kc_u and bb_l > kc_l
    # squeeze release detection: was in squeeze 3 bars ago, now no longer
    sq_3_ago = float(upper.iloc[-3]) < float(kc_upper.iloc[-3]) and float(lower.iloc[-3]) > float(kc_lower.iloc[-3])
    squeeze_release = sq_3_ago and not in_squeeze
    # Walking the upper band (last 5 bars consistently > upper - 0.2σ)
    walking_up = all(c.iloc[-i] > upper.iloc[-i] * 0.998 for i in range(1, 4))
    walking_dn = all(c.iloc[-i] < lower.iloc[-i] * 1.002 for i in range(1, 4))

    bw_contracted = bw < bw_avg * 0.8

    payload = {
        "upper": round(bb_u, 5), "lower": round(bb_l, 5),
        "pct_b": round(pb, 3), "bandwidth": round(bw, 5),
        "bandwidth_pct_avg": round(bw / bw_avg, 2) if bw_avg else None,
        "in_squeeze": in_squeeze, "squeeze_release": squeeze_release,
        "walking_upper": walking_up, "walking_lower": walking_dn,
        "bandwidth_contracted": bw_contracted,
    }

    score = 0.0
    if squeeze_release:
        # direction = sign of recent close move from band middle
        score += 35 if last_c > float(sma20.iloc[-1]) else -35
    if walking_up: score += 22
    if walking_dn: score -= 22
    # Mean reversion when far outside bands without walking
    if pb > 1 and not walking_up: score -= 18
    if pb < 0 and not walking_dn: score += 18
    # Bandwidth still contracted but price probing one side: prepare for breakout
    if bw_contracted and pb > 0.7: score += 8
    if bw_contracted and pb < 0.3: score -= 8

    if score >= 22:
        return AnalyzerResult(CODE, "buy", min(90.0, 50 + score), WEIGHT_DEFAULT, payload)
    if score <= -22:
        return AnalyzerResult(CODE, "sell", min(90.0, 50 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class BollingerBandsSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
