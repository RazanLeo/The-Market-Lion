"""ICT Premium / Equilibrium / Discount — split last major leg into halves.

Major leg = last significant swing high vs swing low (highest/lowest in last 50 bars).
Equilibrium = midpoint.
Above mid = Premium (sell zone bias). Below mid = Discount (buy zone bias).
Sub-zones: 0-50% = Discount, 50-100% = Premium, with deeper sub-bands at 0.62-0.79 OTE.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "equilibrium_premium_discount"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-50:]
    swing_h = float(win["h"].max()); swing_l = float(win["l"].min())
    rng = swing_h - swing_l
    if rng <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    eq = (swing_h + swing_l) / 2
    last = float(df["c"].iloc[-1])
    pos = (last - swing_l) / rng
    if pos > 0.79: zone = "deep_premium"
    elif pos > 0.50: zone = "premium"
    elif pos > 0.21: zone = "discount"
    else: zone = "deep_discount"
    payload = {"swing_high": round(swing_h, 5), "swing_low": round(swing_l, 5),
               "equilibrium": round(eq, 5), "position_pct": round(pos * 100, 1),
               "zone": zone}
    if zone == "deep_discount": return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if zone == "discount": return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if zone == "premium": return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    if zone == "deep_premium": return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class EquilibriumPremiumDiscountAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
