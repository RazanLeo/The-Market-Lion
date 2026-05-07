"""Lion Smart Money Flow — open-vs-close strength on first/last 30 minutes of session.

Smart money is presumed to act in the LAST 30 minutes (closing auction); retail dominates first.
Compute (close - open) over the last 2 bars (final 30m on 15m TF) → smart_money signal.
Compare against (close - open) of first 2 bars of session (retail signal).
Divergence = institutional vs retail going opposite ways.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_smart_money_flow"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if not isinstance(df.index, pd.DatetimeIndex) or len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    today = df.index[-1].normalize()
    today_df = df[df.index >= today]
    if len(today_df) < 4: today_df = df.iloc[-32:]
    first2 = today_df.iloc[:2]
    last2 = today_df.iloc[-2:]
    retail = float(first2["c"].iloc[-1]) - float(first2["o"].iloc[0])
    smart = float(last2["c"].iloc[-1]) - float(last2["o"].iloc[0])
    payload = {"retail_signal": round(retail, 5), "smart_money_signal": round(smart, 5),
               "divergence": (retail * smart) < 0}
    if smart > 0 and abs(smart) > abs(retail):
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if smart < 0 and abs(smart) > abs(retail):
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionSmartMoneyFlowAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
