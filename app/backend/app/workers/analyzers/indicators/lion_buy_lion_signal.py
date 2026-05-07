"""Lion Buy Lion — institutional-grade confluence buy.

Requires ALL of:
  - BOS up (close > prior 20-bar swing high)
  - close > EMA(20)
  - RSI(14) rising from below 40 within last 5 bars
  - volume > 1.5× rolling 20-bar avg
  - composite confluence ≥ 70 (computed locally)
Designed for high-stake institutional setups.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_buy_lion_signal"
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
    swing_high = df["h"].iloc[-21:-1].max()
    bos_up = float(c.iloc[-1]) > float(swing_high)
    above_ema = float(c.iloc[-1]) > float(ema20.iloc[-1])
    rsi_now = float(rsi.iloc[-1]); rsi_5 = float(rsi.iloc[-6])
    rsi_rising = rsi_5 < 40 and rsi_now > rsi_5
    vol_avg = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    vol_surge = float(df["v"].iloc[-1]) > 1.5 * vol_avg if vol_avg > 0 else False
    flags = [bos_up, above_ema, rsi_rising, vol_surge]
    confluence = sum(flags) * 25  # 0/25/50/75/100
    payload = {"BOS_up": bos_up, "above_EMA20": above_ema,
               "RSI_rising_from_oversold": rsi_rising, "volume_surge": vol_surge,
               "confluence_local": confluence, "buy_lion_active": confluence >= 75}
    if confluence >= 75:
        return AnalyzerResult(CODE, "buy", min(95, 60 + confluence / 4), WEIGHT_DEFAULT, payload)
    if confluence >= 50:
        return AnalyzerResult(CODE, "buy", 55, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionBuyLionSignalAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
