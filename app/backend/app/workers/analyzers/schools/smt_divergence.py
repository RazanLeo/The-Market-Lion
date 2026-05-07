"""SMT (Smart Money Tool) Divergence — compare two correlated series for non-confirmation.

Without a second symbol we use a synthetic leader-follower:
  • Leader = SMA(close, 14)
  • Follower = current close
A bullish SMT: follower makes lower-low while leader makes higher-low (or holds).
A bearish SMT: follower higher-high while leader makes lower-high.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "smt_divergence"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    leader = df["c"].rolling(14).mean()
    win = df.iloc[-30:]
    leader_win = leader.iloc[-30:]
    p_high = int(win["c"].argmax()); p_low = int(win["c"].argmin())
    bear_smt = bull_smt = False
    if p_high > 5:
        earlier = int(win["c"].iloc[:p_high].argmax())
        if win["c"].iloc[p_high] > win["c"].iloc[earlier] and leader_win.iloc[p_high] < leader_win.iloc[earlier]:
            bear_smt = True
    if p_low > 5:
        earlier = int(win["c"].iloc[:p_low].argmin())
        if win["c"].iloc[p_low] < win["c"].iloc[earlier] and leader_win.iloc[p_low] > leader_win.iloc[earlier]:
            bull_smt = True
    payload = {"bull_smt": bull_smt, "bear_smt": bear_smt}
    if bull_smt: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if bear_smt: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SmtDivergenceAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
