"""Accumulation/Distribution Tool — A/D line slope + regime label.

A/D line = Σ ((c-l) - (h-c)) / (h-l) × volume
Slope of A/D over rolling 30 bars determines regime: positive = accumulation,
negative = distribution. Draws label badges only (A/D is sub-chart, not price overlay).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "accumulation_distribution_tool"
WEIGHT_DEFAULT = 0.9


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    mfm = ((df["c"] - df["l"]) - (df["h"] - df["c"])) / rng
    mfv = mfm * df["v"]
    ad = mfv.cumsum()
    ad_30 = ad.iloc[-30:]
    slope = (float(ad_30.iloc[-1]) - float(ad_30.iloc[0])) / 30
    ad_avg = abs(float(ad.iloc[-30:].mean())) + 1e-9
    slope_norm = slope / ad_avg
    regime = "accumulation" if slope > 0 else "distribution" if slope < 0 else "balanced"
    last_c = float(df["c"].iloc[-1])
    drawings = [
        {"type": "label", "x": str(df.index[-1]), "y": last_c,
         "text": f"A/D: {regime}", "color": "#16a34a" if slope > 0 else "#dc2626",
         "label": "A/D regime"},
    ]
    price_5b_change = float(df["c"].iloc[-1]) - float(df["c"].iloc[-6])
    bull_div = slope > 0 and price_5b_change < 0
    bear_div = slope < 0 and price_5b_change > 0
    payload = {"drawings": drawings, "ad_slope_30b": round(float(slope), 2),
               "ad_slope_norm": round(float(slope_norm), 4), "regime": regime,
               "bull_divergence_with_price": bull_div, "bear_divergence_with_price": bear_div}
    if bull_div:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if bear_div:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if slope_norm > 0.1 and price_5b_change > 0:
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if slope_norm < -0.1 and price_5b_change < 0:
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AccumulationDistributionToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
