"""Lion Sell Lion — institutional confluence sell.

Mirror of buy_lion: BOS down + close < EMA20 + RSI falling from above 60 + volume surge.
Strong directional setup for institutional shorts.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_sell_lion_signal"
WEIGHT_DEFAULT = 1.3


def _rsi(c, n=14):
    diff = c.diff()
    up = diff.clip(lower=0); dn = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / (ad + 1e-9))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    ema20 = c.ewm(span=20, adjust=False).mean()
    rsi = _rsi(c)
    swing_low = df["l"].iloc[-21:-1].min()
    bos_dn = float(c.iloc[-1]) < float(swing_low)
    below_ema = float(c.iloc[-1]) < float(ema20.iloc[-1])
    rsi_now = float(rsi.iloc[-1]); rsi_5 = float(rsi.iloc[-6])
    rsi_falling = rsi_5 > 60 and rsi_now < rsi_5
    vol_avg = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    vol_surge = float(df["v"].iloc[-1]) > 1.5 * vol_avg if vol_avg > 0 else False
    flags = [bos_dn, below_ema, rsi_falling, vol_surge]
    confluence = sum(flags) * 25
    payload = {"BOS_down": bos_dn, "below_EMA20": below_ema,
               "RSI_falling_from_overbought": rsi_falling, "volume_surge": vol_surge,
               "confluence_local": confluence, "sell_lion_active": confluence >= 75}
    if confluence >= 75:
        return AnalyzerResult(CODE, "sell", min(95, 60 + confluence / 4), WEIGHT_DEFAULT, payload)
    if confluence >= 50:
        return AnalyzerResult(CODE, "sell", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionSellLionSignalAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
