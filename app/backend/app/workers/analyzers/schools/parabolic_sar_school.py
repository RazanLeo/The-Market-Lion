"""Wilder Parabolic SAR — full implementation with AF starting at 0.02 and stepping by 0.02 to 0.20.

SAR formula:
  Long:  SAR[t+1] = SAR[t] + AF × (EP - SAR[t]); EP = highest high in current trend.
  Short: SAR[t+1] = SAR[t] - AF × (SAR[t] - EP); EP = lowest low in current trend.
Reversal when price crosses SAR.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "parabolic_sar_school"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    h, l = df["h"], df["l"]
    sar = float(l.iloc[0]); af = 0.02; ep = float(h.iloc[0]); side = 1  # 1 long, -1 short
    bars_since_reverse = 0
    flips_log = []
    for i in range(1, len(df)):
        cur_h = float(h.iloc[i]); cur_l = float(l.iloc[i])
        if side == 1:
            sar = sar + af * (ep - sar)
            if cur_h > ep:
                ep = cur_h; af = min(af + 0.02, 0.20)
            if cur_l < sar:
                # Reverse
                side = -1; sar = ep; ep = cur_l; af = 0.02
                flips_log.append((i, "to_short", float(sar)))
                bars_since_reverse = 0
            else:
                bars_since_reverse += 1
        else:
            sar = sar - af * (sar - ep)
            if cur_l < ep:
                ep = cur_l; af = min(af + 0.02, 0.20)
            if cur_h > sar:
                side = 1; sar = ep; ep = cur_h; af = 0.02
                flips_log.append((i, "to_long", float(sar)))
                bars_since_reverse = 0
            else:
                bars_since_reverse += 1
    payload = {"sar_now": round(sar, 5), "side": "long" if side == 1 else "short",
               "ep": round(ep, 5), "af_now": round(af, 3),
               "bars_since_reverse": bars_since_reverse,
               "recent_flips": flips_log[-3:] if flips_log else []}
    just_flipped = bars_since_reverse <= 1
    if side == 1:
        return AnalyzerResult(CODE, "buy", 75 if just_flipped else 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "sell", 75 if just_flipped else 50, WEIGHT_DEFAULT, payload)


class ParabolicSarSchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
