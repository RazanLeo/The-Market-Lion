"""John Bollinger — full Bollinger framework: Squeeze (BB inside Keltner) + M-tops / W-bottoms via BB
+ bandwidth percentile rank + %B momentum + walking the bands.

This duplicates none of the other Bollinger logic — it focuses on the M/W reversal pattern (BB classic):
  M-top: price makes high outside upper band, pulls back, makes second high inside band → bearish.
  W-bottom: price makes low outside lower band, recovers, makes second low inside band → bullish.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "john_bollinger_school"
WEIGHT_DEFAULT = 0.95


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    c = df["c"]; h = df["h"]; l = df["l"]
    sma20 = c.rolling(20).mean()
    sd20 = c.rolling(20).std()
    upper = sma20 + 2 * sd20
    lower = sma20 - 2 * sd20
    pct_b = (c - lower) / (upper - lower + 1e-9)
    bw = (upper - lower) / sma20

    # Bandwidth percentile rank
    bw_w = bw.iloc[-100:] if len(bw) >= 100 else bw
    bw_rank = float((bw_w <= bw.iloc[-1]).sum() / len(bw_w))

    # Keltner for squeeze
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr20 = tr.rolling(20).mean()
    e20 = c.ewm(span=20, adjust=False).mean()
    kc_u = e20 + 1.5 * atr20; kc_l = e20 - 1.5 * atr20
    in_squeeze = float(upper.iloc[-1]) < float(kc_u.iloc[-1]) and float(lower.iloc[-1]) > float(kc_l.iloc[-1])

    # M-top: 2 highs in last 20 bars where first high broke upper, second high stayed inside upper
    win = df.iloc[-20:]; bb_u_win = upper.iloc[-20:]
    p1 = int(win["h"].argmax())
    high1 = float(win["h"].iloc[p1]); bb1 = float(bb_u_win.iloc[p1])
    sub_after = win.iloc[p1 + 3:] if p1 + 3 < len(win) else win.iloc[:0]
    m_top = False; w_bot = False
    if len(sub_after) > 3:
        p2 = int(sub_after["h"].argmax())
        high2 = float(sub_after["h"].iloc[p2]); bb2 = float(bb_u_win.iloc[p1 + 3 + p2])
        if high1 > bb1 and high2 > 0.95 * high1 and high2 < bb2:
            m_top = True

    p1l = int(win["l"].argmin())
    low1 = float(win["l"].iloc[p1l]); bb1l = float(lower.iloc[-20:].iloc[p1l])
    sub_after_l = win.iloc[p1l + 3:] if p1l + 3 < len(win) else win.iloc[:0]
    if len(sub_after_l) > 3:
        p2l = int(sub_after_l["l"].argmin())
        low2 = float(sub_after_l["l"].iloc[p2l]); bb2l = float(lower.iloc[-20:].iloc[p1l + 3 + p2l])
        if low1 < bb1l and low2 < 1.05 * low1 and low2 > bb2l:
            w_bot = True

    payload = {"bandwidth_percentile": round(bw_rank, 2),
               "in_squeeze": in_squeeze, "%B": round(float(pct_b.iloc[-1]), 3),
               "M_top_pattern": m_top, "W_bottom_pattern": w_bot}
    if m_top: return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    if w_bot: return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if in_squeeze and bw_rank < 0.20:
        # Pre-breakout: lean toward last close direction
        last_c = float(c.iloc[-1]); s20 = float(sma20.iloc[-1])
        return AnalyzerResult(CODE, "buy" if last_c > s20 else "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class JohnBollingerSchoolAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
