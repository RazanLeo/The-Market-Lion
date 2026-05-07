"""Market Profile (Steidlmayer TPO) — letter-per-period profile, IB, range extension, profile shape.

We treat each bar as a TPO unit and assign a letter A,B,C... to bars within a "session"
(96 bars on 15m = 1 day). For each price bin we count distinct letter visits (TPO count).
  • Initial Balance (IB): high/low of first 4 bars (≈first hour on 15m).
  • Range Extension: subsequent bar high/low beyond IB.
  • Profile shape: D (balanced), b (selling tail), P (buying tail),
                   double-distribution (two peaks).
  • Single Prints: bins with TPO count == 1 — thin liquidity.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "market_profile"
WEIGHT_DEFAULT = 1.0


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 96:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    session = df.iloc[-96:]
    bins = 30
    lo = float(session["l"].min()); hi = float(session["h"].max())
    if hi <= lo:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    edges = np.linspace(lo, hi, bins + 1)
    tpo = np.zeros(bins, dtype=int)
    letters_per_bin: list[set] = [set() for _ in range(bins)]
    for i in range(len(session)):
        bar_lo = float(session["l"].iloc[i]); bar_hi = float(session["h"].iloc[i])
        first = max(0, np.searchsorted(edges, bar_lo, side="right") - 1)
        last_b = min(bins - 1, np.searchsorted(edges, bar_hi, side="right") - 1)
        for b in range(first, last_b + 1):
            letters_per_bin[b].add(i)
            tpo[b] += 1
    poc_idx = int(tpo.argmax())
    poc_price = float((edges[poc_idx] + edges[poc_idx + 1]) / 2)
    # Profile shape
    third = bins // 3
    top = tpo[2 * third:].sum(); mid = tpo[third:2 * third].sum(); bot = tpo[:third].sum()
    total = tpo.sum() or 1
    top_p = top / total; bot_p = bot / total
    if abs(top_p - bot_p) < 0.10 and tpo.std() < tpo.mean() * 0.5: shape = "D_balanced"
    elif top_p > 0.45: shape = "P_buying_tail"
    elif bot_p > 0.45: shape = "b_selling_tail"
    else:
        # Double distribution: two peaks?
        peaks = sum(1 for i in range(1, bins - 1) if tpo[i] > tpo[i - 1] and tpo[i] > tpo[i + 1] and tpo[i] > tpo.mean() * 1.3)
        shape = "double_distribution" if peaks >= 2 else "irregular"
    # IB (first 4 bars)
    ib_high = float(session["h"].iloc[:4].max()); ib_low = float(session["l"].iloc[:4].min())
    last_close = float(df["c"].iloc[-1])
    range_ext_up = float(session["h"].iloc[4:].max()) > ib_high
    range_ext_dn = float(session["l"].iloc[4:].min()) < ib_low
    single_prints = [float((edges[i] + edges[i + 1]) / 2) for i in range(bins) if tpo[i] == 1]
    payload = {"shape": shape, "POC": round(poc_price, 5),
               "IB_high": round(ib_high, 5), "IB_low": round(ib_low, 5),
               "range_extension_up": range_ext_up, "range_extension_down": range_ext_dn,
               "single_prints": [round(x, 5) for x in single_prints][:5]}
    if shape == "P_buying_tail" and range_ext_up:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if shape == "b_selling_tail" and range_ext_dn:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    if last_close > ib_high and range_ext_up: return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    if last_close < ib_low and range_ext_dn: return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MarketProfileAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
