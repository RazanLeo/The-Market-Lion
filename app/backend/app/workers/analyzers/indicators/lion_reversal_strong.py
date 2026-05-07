"""Lion Strong Reversal — pattern + RSI divergence + volume climax.

Triple-confirmation reversal:
  1. Single-bar pattern (pin bar OR engulfing) at swing extreme
  2. RSI divergence (price new low/high but RSI not)
  3. Volume climax: vol > 2× rolling 20-bar avg
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_reversal_strong"
WEIGHT_DEFAULT = 1.25


def _rsi(c, n=14):
    diff = c.diff()
    up = diff.clip(lower=0); dn = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / (ad + 1e-9))


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    o1 = float(df["o"].iloc[-1]); c1 = float(df["c"].iloc[-1])
    h1 = float(df["h"].iloc[-1]); l1 = float(df["l"].iloc[-1])
    body = abs(c1 - o1); rng = h1 - l1 + 1e-9
    upper = h1 - max(o1, c1); lower = min(o1, c1) - l1
    bull_pin = lower > 2 * body
    bear_pin = upper > 2 * body
    rsi = _rsi(df["c"]).iloc[-25:]
    win_p = df["c"].iloc[-25:]
    p_low_idx = int(win_p.argmin()); p_high_idx = int(win_p.argmax())
    rsi_low_idx = int(rsi.argmin()); rsi_high_idx = int(rsi.argmax())
    bull_div = (p_low_idx >= 18 and rsi_low_idx < p_low_idx - 3 and bull_pin)
    bear_div = (p_high_idx >= 18 and rsi_high_idx < p_high_idx - 3 and bear_pin)
    vol_avg = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    vol_climax = float(df["v"].iloc[-1]) > 2 * vol_avg if vol_avg > 0 else False
    bull = bull_div and vol_climax
    bear = bear_div and vol_climax
    payload = {"bull_div+pin": bull_div, "bear_div+pin": bear_div,
               "vol_climax": vol_climax, "rsi_low": float(rsi.iloc[-1]),
               "strong_reversal_active": bull or bear}
    if bull:
        return AnalyzerResult(CODE, "buy", 88, WEIGHT_DEFAULT, payload)
    if bear:
        return AnalyzerResult(CODE, "sell", 88, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionReversalStrongAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
