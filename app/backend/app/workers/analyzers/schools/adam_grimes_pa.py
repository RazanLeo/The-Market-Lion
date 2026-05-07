"""Adam Grimes structured price action — pullback to 20EMA, macro/micro alignment, failure-test.

Setups detected:
  • Pullback Buy (Trend Up): higher-highs/higher-lows + recent 5-bar pullback testing 20EMA + reversal bar.
  • Pullback Sell (Trend Down): mirror.
  • Failure Test: a fresh new high that closes below the prior high (or vice versa).
  • Macro/Micro: 50EMA must agree with 20EMA direction.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "adam_grimes_pa"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()
    macro_up = float(ema50.iloc[-1]) > float(ema50.iloc[-10])
    macro_dn = float(ema50.iloc[-1]) < float(ema50.iloc[-10])
    micro_up = float(ema20.iloc[-1]) > float(ema20.iloc[-5])
    micro_dn = float(ema20.iloc[-1]) < float(ema20.iloc[-5])

    last = float(c.iloc[-1])
    e20 = float(ema20.iloc[-1])
    distance_to_ema = abs(last - e20)
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 1)
    pullback_ema = distance_to_ema < atr * 0.6

    # Failure test: high > recent_swing_high and close < recent_swing_high
    sw_high_20 = float(df["h"].iloc[-20:-1].max())
    sw_low_20 = float(df["l"].iloc[-20:-1].min())
    last_h = float(df["h"].iloc[-1])
    last_l = float(df["l"].iloc[-1])
    fail_test_top = last_h > sw_high_20 and last < sw_high_20
    fail_test_bot = last_l < sw_low_20 and last > sw_low_20

    # Reversal bar at EMA pullback
    o = float(df["o"].iloc[-1])
    rev_up_bar = pullback_ema and last > o and last > (last_l + (last_h - last_l) * 0.7)
    rev_dn_bar = pullback_ema and last < o and last < (last_l + (last_h - last_l) * 0.3)

    payload = {"macro_up": macro_up, "macro_dn": macro_dn,
               "micro_up": micro_up, "micro_dn": micro_dn,
               "pullback_to_ema20": pullback_ema,
               "failure_test_top": fail_test_top, "failure_test_bottom": fail_test_bot,
               "reversal_bar_up": rev_up_bar, "reversal_bar_dn": rev_dn_bar,
               "stop_suggestion_long": round(last_l - atr * 0.2, 5),
               "stop_suggestion_short": round(last_h + atr * 0.2, 5)}

    if macro_up and micro_up and pullback_ema and rev_up_bar:
        return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if macro_dn and micro_dn and pullback_ema and rev_dn_bar:
        return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    if fail_test_top: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if fail_test_bot: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AdamGrimesPaAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
