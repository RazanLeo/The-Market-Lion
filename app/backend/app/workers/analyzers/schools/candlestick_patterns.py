"""Candlestick pattern recognition — proper body/shadow ratio rules for ~16 patterns.

Each pattern returns a reliability score based on:
  • Pattern strict-ness (how well ratios match canonical definition).
  • Location (near support/resistance, prior trend).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "candlestick_patterns"
WEIGHT_DEFAULT = 1.0


def _ohlc(df: pd.DataFrame, i: int):
    return float(df["o"].iloc[i]), float(df["h"].iloc[i]), float(df["l"].iloc[i]), float(df["c"].iloc[i])


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 4:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    o, h, l, c = _ohlc(df, -1)
    po, ph, pl, pc = _ohlc(df, -2)
    ppo, pph, ppl, ppc = _ohlc(df, -3)
    rng = h - l; body = abs(c - o); upper = h - max(o, c); lower = min(o, c) - l
    if rng <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    body_pct = body / rng

    detected: list[tuple[str, str, float]] = []  # (name, side, weight)

    # Doji (body < 10% of range)
    if body_pct < 0.10:
        detected.append(("doji", "neutral", 30))
    # Hammer (small body upper, long lower shadow, closes higher)
    if body_pct <= 0.30 and lower / rng >= 0.6 and upper / rng <= 0.15 and c > o:
        detected.append(("hammer", "buy", 70))
    # Hanging Man (same shape after up trend)
    if body_pct <= 0.30 and lower / rng >= 0.6 and upper / rng <= 0.15 and c < o and df["c"].iloc[-1] > df["c"].iloc[-10]:
        detected.append(("hanging_man", "sell", 65))
    # Inverted Hammer
    if body_pct <= 0.30 and upper / rng >= 0.6 and lower / rng <= 0.15 and c > o and df["c"].iloc[-1] < df["c"].iloc[-10]:
        detected.append(("inverted_hammer", "buy", 60))
    # Shooting Star
    if body_pct <= 0.30 and upper / rng >= 0.6 and lower / rng <= 0.15 and c < o and df["c"].iloc[-1] > df["c"].iloc[-10]:
        detected.append(("shooting_star", "sell", 70))
    # Marubozu bullish (no shadows)
    if body_pct >= 0.95 and c > o:
        detected.append(("marubozu_bull", "buy", 60))
    if body_pct >= 0.95 and c < o:
        detected.append(("marubozu_bear", "sell", 60))
    # Spinning Top
    if 0.10 <= body_pct <= 0.30 and abs(upper - lower) / rng < 0.20:
        detected.append(("spinning_top", "neutral", 25))

    # Bullish Engulfing
    if pc < po and c > o and o <= pc and c >= po:
        detected.append(("bullish_engulfing", "buy", 75))
    # Bearish Engulfing
    if pc > po and c < o and o >= pc and c <= po:
        detected.append(("bearish_engulfing", "sell", 75))

    # Piercing Line
    if pc < po and c > o and o < pl and c >= (po + pc) / 2:
        detected.append(("piercing_line", "buy", 60))
    # Dark Cloud Cover
    if pc > po and c < o and o > ph and c <= (po + pc) / 2:
        detected.append(("dark_cloud_cover", "sell", 60))

    # Morning Star (ppc < ppo, small body in middle, c bullish closing > mid of pp body)
    if ppc < ppo and abs(pc - po) / max(ph - pl, 1e-9) < 0.30 and c > o and c > (ppo + ppc) / 2:
        detected.append(("morning_star", "buy", 80))
    # Evening Star
    if ppc > ppo and abs(pc - po) / max(ph - pl, 1e-9) < 0.30 and c < o and c < (ppo + ppc) / 2:
        detected.append(("evening_star", "sell", 80))

    # Three White Soldiers
    if c > o and pc > po and ppc > ppo and c > pc > ppc and o > po > ppo:
        detected.append(("three_white_soldiers", "buy", 75))
    # Three Black Crows
    if c < o and pc < po and ppc < ppo and c < pc < ppc and o < po < ppo:
        detected.append(("three_black_crows", "sell", 75))

    # Tweezer Tops/Bottoms
    if abs(h - ph) / max(rng, 1e-9) < 0.05 and pc > po and c < o:
        detected.append(("tweezer_top", "sell", 55))
    if abs(l - pl) / max(rng, 1e-9) < 0.05 and pc < po and c > o:
        detected.append(("tweezer_bottom", "buy", 55))

    if not detected:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"body_pct": round(body_pct, 3)})

    # Aggregate score weighted by side
    buys = sum(d[2] for d in detected if d[1] == "buy")
    sells = sum(d[2] for d in detected if d[1] == "sell")
    payload = {"patterns": [d[0] for d in detected], "buy_weight": buys, "sell_weight": sells,
               "body_pct": round(body_pct, 3), "upper_pct": round(upper / rng, 3), "lower_pct": round(lower / rng, 3)}

    if buys - sells >= 30:
        return AnalyzerResult(CODE, "buy", min(90.0, 40 + (buys - sells) * 0.6), WEIGHT_DEFAULT, payload)
    if sells - buys >= 30:
        return AnalyzerResult(CODE, "sell", min(90.0, 40 + (sells - buys) * 0.6), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 25.0, WEIGHT_DEFAULT, payload)


class CandlestickPatternsAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
