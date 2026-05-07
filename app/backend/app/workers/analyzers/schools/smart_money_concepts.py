"""Smart Money Concepts (SMC) — composite SMC score = BOS + CHoCH + OB + FVG.

Returns a single confluence score combining all 4 SMC primitives.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "smart_money_concepts"
WEIGHT_DEFAULT = 1.25


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_c = float(df["c"].iloc[-1])
    swing_high = float(df["h"].iloc[-21:-1].max())
    swing_low = float(df["l"].iloc[-21:-1].min())
    bos_up = last_c > swing_high; bos_dn = last_c < swing_low
    # CHoCH: recent BOS direction is reversed
    prev_swing_high = float(df["h"].iloc[-42:-22].max())
    prev_swing_low = float(df["l"].iloc[-42:-22].min())
    choch_up = float(df["c"].iloc[-15]) < prev_swing_low and last_c > swing_high
    choch_dn = float(df["c"].iloc[-15]) > prev_swing_high and last_c < swing_low
    # OB
    atr_s = _atr(df)
    ob_buy = ob_sell = False
    for i in range(len(df) - 20, len(df) - 5):
        atr_i = float(atr_s.iloc[i] or 0)
        if atr_i <= 0: continue
        body_dir = float(df["c"].iloc[i]) - float(df["o"].iloc[i])
        net = float(df["c"].iloc[i + 5]) - float(df["c"].iloc[i])
        if body_dir < 0 and net > 2 * atr_i and float(df["l"].iloc[i]) <= last_c <= float(df["h"].iloc[i]):
            ob_buy = True
        elif body_dir > 0 and net < -2 * atr_i and float(df["l"].iloc[i]) <= last_c <= float(df["h"].iloc[i]):
            ob_sell = True
    # FVG
    fvg_up = fvg_dn = False
    for i in range(len(df) - 12, len(df) - 1):
        if float(df["h"].iloc[i - 1]) < float(df["l"].iloc[i + 1]): fvg_up = True
        if float(df["l"].iloc[i - 1]) > float(df["h"].iloc[i + 1]): fvg_dn = True
    bull_score = sum([bos_up, choch_up, ob_buy, fvg_up])
    bear_score = sum([bos_dn, choch_dn, ob_sell, fvg_dn])
    payload = {"BOS_up": bos_up, "BOS_dn": bos_dn, "CHoCH_up": choch_up, "CHoCH_dn": choch_dn,
               "OB_buy": ob_buy, "OB_sell": ob_sell, "FVG_up": fvg_up, "FVG_dn": fvg_dn,
               "bull_smc_score": bull_score, "bear_smc_score": bear_score}
    if bull_score >= 3:
        return AnalyzerResult(CODE, "buy", min(90, 55 + bull_score * 10), WEIGHT_DEFAULT, payload)
    if bear_score >= 3:
        return AnalyzerResult(CODE, "sell", min(90, 55 + bear_score * 10), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SmartMoneyConceptsAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
