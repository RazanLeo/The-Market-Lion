"""Order Flow School — Cumulative Volume Delta (CVD), aggressive concentration, divergence detection.

CVD computed per bar as sign(close - open) × volume. Cumulative sum over window.
Divergence: price higher-high but CVD lower-high → bearish divergence (and mirror).
Aggressive concentration: latest 5 bars' delta vs 50-bar avg.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "order_flow"
WEIGHT_DEFAULT = 1.05


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    delta = np.sign(df["c"] - df["o"]) * df["v"].fillna(0)
    cvd = delta.cumsum()
    win = df.iloc[-30:]
    cvd_win = cvd.iloc[-30:]
    p_high = int(win["c"].argmax()); p_low = int(win["c"].argmin())
    bear_div = bull_div = False
    if p_high > 5:
        earlier = int(win["c"].iloc[:p_high].argmax())
        if win["c"].iloc[p_high] > win["c"].iloc[earlier] and cvd_win.iloc[p_high] < cvd_win.iloc[earlier]:
            bear_div = True
    if p_low > 5:
        earlier = int(win["c"].iloc[:p_low].argmin())
        if win["c"].iloc[p_low] < win["c"].iloc[earlier] and cvd_win.iloc[p_low] > cvd_win.iloc[earlier]:
            bull_div = True
    last_5_delta = float(delta.iloc[-5:].sum())
    avg_50_delta = float(delta.iloc[-50:].mean() * 5)
    concentration_ratio = last_5_delta / avg_50_delta if avg_50_delta else 0
    aggressive_buying = last_5_delta > 0 and abs(last_5_delta) > abs(avg_50_delta) * 2
    aggressive_selling = last_5_delta < 0 and abs(last_5_delta) > abs(avg_50_delta) * 2
    payload = {"cvd_now": float(cvd.iloc[-1]), "cvd_30bars_change": float(cvd.iloc[-1] - cvd.iloc[-30]),
               "bull_divergence": bull_div, "bear_divergence": bear_div,
               "last_5_delta": last_5_delta, "avg_50_delta": avg_50_delta,
               "aggressive_buying": aggressive_buying, "aggressive_selling": aggressive_selling}
    score = 0
    if bull_div: score += 35
    if bear_div: score -= 35
    if aggressive_buying: score += 25
    if aggressive_selling: score -= 25
    if score >= 25: return AnalyzerResult(CODE, "buy", min(85.0, 50 + score), WEIGHT_DEFAULT, payload)
    if score <= -25: return AnalyzerResult(CODE, "sell", min(85.0, 50 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class OrderFlowAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
