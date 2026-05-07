"""ICT Full — comprehensive ICT setup combining BOS + OB + FVG + Killzone confirmation.

A full ICT trade setup requires:
  • BOS (break of structure)
  • Mitigated order block touched
  • Fair value gap above/below current price (target)
  • Bar within ICT killzone (London/NY open hours)
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "ict_full"
WEIGHT_DEFAULT = 1.2


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_c = float(df["c"].iloc[-1])
    swing_high = float(df["h"].iloc[-21:-1].max())
    swing_low = float(df["l"].iloc[-21:-1].min())
    bos_up = last_c > swing_high; bos_dn = last_c < swing_low
    # OB: last opposite candle before > 2×ATR move
    atr_s = _atr(df)
    ob_buy = ob_sell = False
    for i in range(len(df) - 20, len(df) - 5):
        atr_i = float(atr_s.iloc[i] or 0)
        if atr_i <= 0: continue
        body_dir = float(df["c"].iloc[i]) - float(df["o"].iloc[i])
        net = float(df["c"].iloc[i + 5]) - float(df["c"].iloc[i])
        if body_dir < 0 and net > 2 * atr_i:
            if float(df["l"].iloc[i]) <= last_c <= float(df["h"].iloc[i]):
                ob_buy = True
        elif body_dir > 0 and net < -2 * atr_i:
            if float(df["l"].iloc[i]) <= last_c <= float(df["h"].iloc[i]):
                ob_sell = True
    # FVG: 3-candle gap
    fvg_up = fvg_dn = False
    for i in range(len(df) - 12, len(df) - 1):
        if float(df["h"].iloc[i - 1]) < float(df["l"].iloc[i + 1]):
            fvg_up = True
        if float(df["l"].iloc[i - 1]) > float(df["h"].iloc[i + 1]):
            fvg_dn = True
    # Killzone: London 07-10 UTC, NY 12-15 UTC
    hr = df.index[-1].hour
    in_kz = (7 <= hr <= 10) or (12 <= hr <= 15)
    score = sum([bos_up, ob_buy, fvg_up, in_kz]) - sum([bos_dn, ob_sell, fvg_dn])
    payload = {"BOS_up": bos_up, "BOS_dn": bos_dn, "OB_buy": ob_buy, "OB_sell": ob_sell,
               "FVG_up": fvg_up, "FVG_dn": fvg_dn, "in_killzone": in_kz, "score": score}
    if score >= 3:
        return AnalyzerResult(CODE, "buy", min(90, 60 + score * 8), WEIGHT_DEFAULT, payload)
    if score <= -3:
        return AnalyzerResult(CODE, "sell", min(90, 60 + abs(score) * 8), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class IctFullAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
