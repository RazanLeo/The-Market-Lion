"""Lion Buy Cub — small green arrow under bar.

Trigger: RSI(14) < 35 AND close > prev close AND bar within 0.6×ATR(14) of recent swing low.
Designed for cub/retail traders ($100-$5000 size). Conservative entries near support.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_buy_cub"
WEIGHT_DEFAULT = 0.95


def _rsi(c: pd.Series, n: int = 14) -> pd.Series:
    diff = c.diff()
    up = diff.clip(lower=0); dn = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    rs = au / (ad + 1e-9)
    return 100 - 100 / (1 + rs)


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rsi = _rsi(df["c"]).iloc[-1]
    atr = float(_atr(df).iloc[-1] or 0)
    last_c = float(df["c"].iloc[-1]); prev_c = float(df["c"].iloc[-2])
    swing_low = float(df["l"].iloc[-20:].min())
    near_low = (last_c - swing_low) <= 0.6 * atr
    cond_rsi = rsi < 35
    cond_up = last_c > prev_c
    active = bool(cond_rsi and cond_up and near_low)
    payload = {"rsi": round(float(rsi), 2), "near_swing_low": near_low,
               "atr": round(atr, 5), "swing_low": round(swing_low, 5),
               "buy_cub_signal": active}
    if active:
        conf = 50 + (35 - float(rsi)) * 1.5  # deeper oversold = higher conf
        return AnalyzerResult(CODE, "buy", min(80, conf), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionBuyCubAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
