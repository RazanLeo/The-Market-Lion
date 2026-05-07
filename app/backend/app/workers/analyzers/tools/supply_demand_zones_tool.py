"""Supply / Demand Zones Tool — RBR / DBD / RBD / DBR base detection + drawings.

A "base" = 1-5 consolidation bars whose total range ≤ 0.6×ATR(14).
Leg = bar with body ≥ 1.5×ATR.
Zone rectangle from base.high to base.low. Color: green for demand (RBR/DBR),
red for supply (DBD/RBD). 'Fresh' tag = price hasn't returned to it.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "supply_demand_zones_tool"
WEIGHT_DEFAULT = 1.2


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    atr = _atr(df)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    body = (df["c"] - df["o"]).abs()
    explosive = body > atr * 1.5
    zones = []
    i = len(df) - 5
    while i > 8:
        if not explosive.iloc[i]:
            i -= 1; continue
        base_end = i - 1; base_start = base_end
        while base_start > base_end - 5 and base_start > 5:
            range_so_far = df["h"].iloc[base_start:base_end + 1].max() - df["l"].iloc[base_start:base_end + 1].min()
            if range_so_far > atr * 0.6:
                base_start += 1; break
            if explosive.iloc[base_start - 1]:
                break
            base_start -= 1
        if base_start >= base_end or base_start < 1 or not explosive.iloc[base_start - 1]:
            i -= 1; continue
        leg1 = +1 if df["c"].iloc[base_start - 1] > df["o"].iloc[base_start - 1] else -1
        leg2 = +1 if df["c"].iloc[i] > df["o"].iloc[i] else -1
        z_high = float(df["h"].iloc[base_start:base_end + 1].max())
        z_low = float(df["l"].iloc[base_start:base_end + 1].min())
        post = df.iloc[i + 1:]
        fresh = True
        if len(post):
            fresh = post["l"].min() > z_low if leg2 > 0 else post["h"].max() < z_high
        ptype = ("RBR" if leg1 > 0 and leg2 > 0 else "DBD" if leg1 < 0 and leg2 < 0 else
                 "RBD" if leg1 > 0 and leg2 < 0 else "DBR")
        kind = "demand" if leg2 > 0 else "supply"
        zones.append({"type": ptype, "kind": kind, "high": z_high, "low": z_low,
                      "start": int(base_start), "end": int(i), "fresh": fresh})
        i = base_start - 2
    drawings = []
    for z in zones[:5]:
        col = "rgba(34,197,94,0.22)" if z["kind"] == "demand" else "rgba(239,68,68,0.22)"
        drawings.append({"type": "rect", "x1": str(df.index[z["start"]]),
                         "y1": z["low"], "x2": str(df.index[-1]), "y2": z["high"],
                         "color": col,
                         "label": f"{z['type']}{' [F]' if z['fresh'] else ''}"})
    last_c = float(df["c"].iloc[-1])
    in_demand = any(z["kind"] == "demand" and z["low"] <= last_c <= z["high"] and z["fresh"] for z in zones)
    in_supply = any(z["kind"] == "supply" and z["low"] <= last_c <= z["high"] and z["fresh"] for z in zones)
    payload = {"drawings": drawings, "zones_total": len(zones),
               "in_fresh_demand": in_demand, "in_fresh_supply": in_supply}
    if in_demand:
        return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if in_supply:
        return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SupplyDemandZonesToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
