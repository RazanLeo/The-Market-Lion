"""CANSLIM (William O'Neil) — price-action proxies for the 7 letters.

Letters mapped to OHLCV-derivable signals:
  C = Current quarterly EPS surge → 13-period ROC > 20% (no fundamentals available).
  A = Annual gain → 52-period ROC > 25%.
  N = New high → close ≥ 52-period high × 0.99.
  S = Supply/Demand → narrow-range bar with high volume (proxy for institutional accumulation).
  L = Leader vs market → close > SMA200 by ≥ 5%.
  I = Institutional sponsorship → recent volume spike > 1.5× 50-bar avg on up bar.
  M = Market direction → SMA50 > SMA200 (proxy for "M is the market").
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "canslim_oneill"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 220 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]; v = df["v"].fillna(0); h = df["h"]; l = df["l"]
    last = float(c.iloc[-1])
    roc13 = (last - float(c.iloc[-14])) / float(c.iloc[-14]) * 100
    roc52 = (last - float(c.iloc[-53])) / float(c.iloc[-53]) * 100
    high52 = float(h.iloc[-52:].max())
    sma50 = float(c.rolling(50).mean().iloc[-1])
    sma200 = float(c.rolling(200).mean().iloc[-1])
    # narrow range bar
    last_range = float(h.iloc[-1] - l.iloc[-1])
    avg_range = float((h - l).rolling(20).mean().iloc[-1])
    avg_vol = float(v.rolling(50).mean().iloc[-1] or 1)
    last_v = float(v.iloc[-1])

    C = roc13 > 20
    A = roc52 > 25
    N = last >= high52 * 0.99
    S = last_range < avg_range * 0.7 and last_v > avg_vol * 1.3
    L = last > sma200 * 1.05
    I = last_v > avg_vol * 1.5 and last > float(c.iloc[-2])
    M = sma50 > sma200
    score = sum([C, A, N, S, L, I, M])
    payload = {"C_quarterly_eps_proxy": C, "A_annual_gain": A, "N_new_high": N,
               "S_supply_demand": S, "L_leader_vs_market": L,
               "I_institutional": I, "M_market_direction": M,
               "score_out_of_7": score, "roc13": round(roc13, 1), "roc52": round(roc52, 1)}
    if score >= 5: return AnalyzerResult(CODE, "buy", min(90.0, 40 + score * 10), WEIGHT_DEFAULT, payload)
    if score <= 1 and not M: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CanslimOneillAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
