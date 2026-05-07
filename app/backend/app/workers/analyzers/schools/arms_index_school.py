"""Arms Index (TRIN) — proxy on a single instrument:

Standard TRIN = (advancers / decliners) / (adv_volume / dec_volume).
We approximate with a per-bar proxy: treat each bar as either an advancer or decliner relative
to the previous close, and weight by its volume.

For the last 30 bars:
   adv = count of bars where close > prev close
   dec = count of bars where close < prev close
   adv_vol = sum volume of advancing bars
   dec_vol = sum volume of declining bars
   trin = (adv/dec) / (adv_vol/dec_vol)

trin > 1.2 → bearish breadth
trin < 0.8 → bullish breadth
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "arms_index_school"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-30:]
    adv = (win["c"] > win["c"].shift()).fillna(False)
    dec = (win["c"] < win["c"].shift()).fillna(False)
    n_adv = int(adv.sum()); n_dec = int(dec.sum())
    if n_adv == 0 or n_dec == 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    v_adv = float(win["v"][adv].sum() or 1); v_dec = float(win["v"][dec].sum() or 1)
    trin = (n_adv / n_dec) / (v_adv / v_dec)
    payload = {"trin": round(float(trin), 3),
               "adv_bars": n_adv, "dec_bars": n_dec,
               "adv_vol": round(v_adv, 2), "dec_vol": round(v_dec, 2)}
    if trin < 0.8:
        return AnalyzerResult(CODE, "buy", min(70.0, 40 + (1 - trin) * 60), WEIGHT_DEFAULT, payload)
    if trin > 1.2:
        return AnalyzerResult(CODE, "sell", min(70.0, 40 + (trin - 1) * 40), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class ArmsIndexSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
