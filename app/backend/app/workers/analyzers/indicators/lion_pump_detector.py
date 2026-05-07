"""Lion PUMP Detector — sustained rally.

Trigger: 5 consecutive bars all close > prev close AND total move >= 3×ATR(14)
        AND volume in last 5 bars rising (avg of last 3 > avg of prior 2).
Detects coordinated upward continuation — possible markup phase.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_pump_detector"
WEIGHT_DEFAULT = 1.0


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    closes = df["c"].iloc[-6:]
    consec_up = all(float(closes.iloc[i]) > float(closes.iloc[i - 1]) for i in range(1, 6))
    total_move = float(closes.iloc[-1]) - float(closes.iloc[0])
    atr = float(_atr(df).iloc[-1] or 0)
    big_move = total_move >= 3 * atr if atr > 0 else False
    vol5 = df["v"].iloc[-5:]
    vol_rising = float(vol5.iloc[-3:].mean()) > float(vol5.iloc[:2].mean())
    pump = consec_up and big_move and vol_rising
    duration = 5 if pump else 0
    if pump:
        # extend duration backwards
        for i in range(len(df) - 7, 0, -1):
            if float(df["c"].iloc[i]) > float(df["c"].iloc[i - 1]):
                duration += 1
            else:
                break
    payload = {"consecutive_up_5b": consec_up, "move_>=3_ATR": big_move,
               "vol_rising": vol_rising, "pump_active": pump, "duration_bars": duration}
    if pump:
        return AnalyzerResult(CODE, "buy", min(85, 55 + duration * 3), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionPumpDetectorAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
