"""Lion Sell Cub — small red arrow above bar.

Mirror of buy_cub: RSI(14) > 65 AND close < prev close AND within 0.6×ATR of recent
swing high. Conservative shorts at resistance.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_sell_cub"
WEIGHT_DEFAULT = 0.95


def _rsi(c, n=14):
    diff = c.diff()
    up = diff.clip(lower=0); dn = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / (ad + 1e-9))


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    rsi = float(_rsi(df["c"]).iloc[-1])
    atr = float(_atr(df).iloc[-1] or 0)
    last_c = float(df["c"].iloc[-1]); prev_c = float(df["c"].iloc[-2])
    swing_high = float(df["h"].iloc[-20:].max())
    near_high = (swing_high - last_c) <= 0.6 * atr
    active = bool(rsi > 65 and last_c < prev_c and near_high)
    payload = {"rsi": round(rsi, 2), "near_swing_high": near_high,
               "atr": round(atr, 5), "swing_high": round(swing_high, 5),
               "sell_cub_signal": active}
    if active:
        conf = 50 + (rsi - 65) * 1.5
        return AnalyzerResult(CODE, "sell", min(80, conf), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionSellCubAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
