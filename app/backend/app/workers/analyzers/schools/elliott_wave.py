"""Elliott Wave Theory — 5-impulse + 3-corrective with Fibonacci validation.

Pipeline:
  1. ZigZag with min %swing = max(0.5×ATR%, 0.8%) of close to identify pivots.
  2. Take last 5 pivots and test motive-wave rules:
       (i)   wave2 retraces 50–78.6% of wave1 and does NOT exceed wave1's start.
       (ii)  wave3 ≥ 1.618 × wave1, and wave3 is NOT the shortest of waves 1/3/5.
       (iii) wave4 retraces 23.6–38.2% of wave3 and does NOT enter wave1's territory.
       (iv)  wave5 ≈ wave1 (0.618–1.618), commonly equal to wave1 or 0.618×(wave1+wave3).
  3. Determine current position (wave 1/2/3/4/5 or A/B/C of correction).
  4. Project the next wave's target using Fibonacci.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "elliott_wave"
WEIGHT_DEFAULT = 1.2


def _zigzag(closes: np.ndarray, atr_val: float, min_pct: float = 0.008):
    if len(closes) < 10: return []
    threshold = max(atr_val * 1.0, closes[-1] * min_pct)
    pivots = [(0, float(closes[0]))]
    direction = 0
    last_idx, last_price = 0, float(closes[0])
    for i in range(1, len(closes)):
        p = float(closes[i])
        if direction >= 0 and p > last_price:
            last_idx, last_price = i, p
        elif direction <= 0 and p < last_price:
            last_idx, last_price = i, p
        if direction in (0, 1) and last_price - p >= threshold:
            pivots.append((last_idx, last_price)); direction = -1
            last_idx, last_price = i, p
        elif direction in (0, -1) and p - last_price >= threshold:
            pivots.append((last_idx, last_price)); direction = 1
            last_idx, last_price = i, p
    pivots.append((last_idx, last_price))
    return pivots


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    closes = df["c"].to_numpy()
    atr_v = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 0)
    pivots = _zigzag(closes, atr_v)
    if len(pivots) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"pivots": len(pivots)})
    last = pivots[-6:] if len(pivots) >= 6 else pivots[-5:]
    if len(last) < 5: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    legs = [last[i+1][1] - last[i][1] for i in range(len(last) - 1)]
    if len(legs) < 4: return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    bull = legs[0] > 0 and legs[1] < 0 and legs[2] > 0 and legs[3] < 0 and (len(legs) < 5 or legs[4] > 0)
    bear = legs[0] < 0 and legs[1] > 0 and legs[2] < 0 and legs[3] > 0 and (len(legs) < 5 or legs[4] < 0)

    payload = {"legs": [round(x, 5) for x in legs], "pivots": len(pivots)}
    if not (bull or bear):
        corr_bull = legs[0] > 0 and legs[1] < 0 and legs[2] > 0
        corr_bear = legs[0] < 0 and legs[1] > 0 and legs[2] < 0
        if corr_bull or corr_bear:
            payload["pattern"] = "ABC_correction"
            return AnalyzerResult(CODE, "neutral", 30, WEIGHT_DEFAULT, payload)
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)

    w1, w2, w3, w4 = abs(legs[0]), abs(legs[1]), abs(legs[2]), abs(legs[3])
    w5 = abs(legs[4]) if len(legs) >= 5 else 0
    rule_w2 = 0.5 * w1 <= w2 <= 0.786 * w1
    rule_w3 = w3 >= 1.618 * w1 and w3 >= max(w1, w5)
    rule_w4 = 0.236 * w3 <= w4 <= 0.382 * w3
    rule_w4_no_overlap = (last[3][1] > last[1][1]) if bull else (last[3][1] < last[1][1])
    rule_w5 = (0.618 * w1 <= w5 <= 1.618 * w1) if w5 > 0 else True
    rules_passed = sum([rule_w2, rule_w3, rule_w4, rule_w4_no_overlap, rule_w5])

    payload.update({"w1": round(w1, 5), "w2": round(w2, 5), "w3": round(w3, 5),
                    "w4": round(w4, 5), "w5": round(w5, 5),
                    "rule_w2_50_786": rule_w2, "rule_w3_1618": rule_w3,
                    "rule_w4_236_382": rule_w4, "rule_w4_no_overlap": rule_w4_no_overlap,
                    "rule_w5_eq_w1": rule_w5, "rules_passed": rules_passed})

    if rules_passed >= 4 and len(legs) >= 5:
        target = last[-1][1] - w5 * 0.618 if bull else last[-1][1] + w5 * 0.618
        payload["next"] = "ABC_correction"; payload["target"] = round(float(target), 5)
        return AnalyzerResult(CODE, "sell" if bull else "buy", min(80.0, 50 + rules_passed * 8), WEIGHT_DEFAULT, payload)
    if rules_passed >= 3:
        target = last[-1][1] + w3 * 0.618 if bull else last[-1][1] - w3 * 0.618
        payload["wave"] = "3_in_progress"; payload["target"] = round(float(target), 5)
        return AnalyzerResult(CODE, "buy" if bull else "sell", min(80.0, 50 + rules_passed * 10), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "buy" if bull else "sell", 30 + rules_passed * 5, WEIGHT_DEFAULT, payload)


class ElliottWaveAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
