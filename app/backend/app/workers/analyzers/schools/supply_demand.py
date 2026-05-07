"""Supply / Demand zones (Sam Seiden style) — RBR / DBD / RBD / DBR base detection.

A "base" = 1-5 consolidation bars whose total range ≤ 0.6×ATR(14).
A "leg"  = one explosive bar with body ≥ 1.5×ATR(14) and same-direction follow-through.
Zone = high-low of the base.

Pattern types:
  • Rally-Base-Rally (RBR)  → BULLISH demand zone (continuation)
  • Drop-Base-Drop  (DBD)   → BEARISH supply zone (continuation)
  • Rally-Base-Drop (RBD)   → BEARISH supply zone (reversal)
  • Drop-Base-Rally (DBR)   → BULLISH demand zone (reversal)

A zone is "fresh" if price has not revisited it since formation. Freshness adds 15 score.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "supply_demand"
WEIGHT_DEFAULT = 1.2


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1] or 0)


def _zones(df: pd.DataFrame) -> list[dict]:
    if len(df) < 60:
        return []
    atr = _atr(df, 14)
    if atr <= 0:
        return []
    body = (df["c"] - df["o"]).abs()
    explosive = body > atr * 1.5
    out: list[dict] = []
    i = len(df) - 5
    while i > 8:
        if not explosive.iloc[i]:
            i -= 1; continue
        base_end = i - 1
        base_start = base_end
        while base_start > base_end - 5 and base_start > 5:
            range_so_far = df["h"].iloc[base_start:base_end + 1].max() - df["l"].iloc[base_start:base_end + 1].min()
            if range_so_far > atr * 0.6:
                base_start += 1; break
            if explosive.iloc[base_start - 1]:
                break
            base_start -= 1
        if base_start >= base_end:
            i -= 1; continue
        if base_start < 1 or not explosive.iloc[base_start - 1]:
            i -= 1; continue
        leg1_dir = +1 if df["c"].iloc[base_start - 1] > df["o"].iloc[base_start - 1] else -1
        leg2_dir = +1 if df["c"].iloc[i] > df["o"].iloc[i] else -1
        zone_high = float(df["h"].iloc[base_start:base_end + 1].max())
        zone_low = float(df["l"].iloc[base_start:base_end + 1].min())
        post = df.iloc[i + 1:]
        fresh = True
        if len(post):
            if leg2_dir > 0:
                fresh = post["l"].min() > zone_low
            else:
                fresh = post["h"].max() < zone_high
        ptype = ("RBR" if leg1_dir > 0 and leg2_dir > 0 else
                 "DBD" if leg1_dir < 0 and leg2_dir < 0 else
                 "RBD" if leg1_dir > 0 and leg2_dir < 0 else "DBR")
        zone_kind = "demand" if leg2_dir > 0 else "supply"
        out.append({"type": ptype, "kind": zone_kind, "high": zone_high, "low": zone_low,
                    "leg2_bar": int(i), "fresh": fresh})
        i = base_start - 2
    return out


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    zones = _zones(df)
    if not zones:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    last_close = float(df["c"].iloc[-1])
    atr = _atr(df, 14)
    demand = [z for z in zones if z["kind"] == "demand" and z["low"] <= last_close + atr * 0.5]
    supply = [z for z in zones if z["kind"] == "supply" and z["high"] >= last_close - atr * 0.5]
    nearest_demand = max(demand, key=lambda z: z["low"]) if demand else None
    nearest_supply = min(supply, key=lambda z: z["high"]) if supply else None
    in_demand = nearest_demand and (nearest_demand["low"] - atr * 0.2) <= last_close <= (nearest_demand["high"] + atr * 0.2)
    in_supply = nearest_supply and (nearest_supply["low"] - atr * 0.2) <= last_close <= (nearest_supply["high"] + atr * 0.2)
    payload = {"zones_total": len(zones),
               "fresh_demand": len([z for z in zones if z["kind"] == "demand" and z["fresh"]]),
               "fresh_supply": len([z for z in zones if z["kind"] == "supply" and z["fresh"]]),
               "nearest_demand": ({**nearest_demand, "high": round(nearest_demand["high"], 5),
                                   "low": round(nearest_demand["low"], 5)} if nearest_demand else None),
               "nearest_supply": ({**nearest_supply, "high": round(nearest_supply["high"], 5),
                                   "low": round(nearest_supply["low"], 5)} if nearest_supply else None),
               "in_demand_zone": bool(in_demand), "in_supply_zone": bool(in_supply)}
    score = 0.0
    if in_demand:
        score += 35 + (15 if nearest_demand["fresh"] else 0)
        if nearest_demand["type"] == "DBR": score += 8
    if in_supply:
        score -= 35 + (15 if nearest_supply["fresh"] else 0)
        if nearest_supply["type"] == "RBD": score -= 8
    if score >= 25:
        return AnalyzerResult(CODE, "buy", min(90.0, 50 + score), WEIGHT_DEFAULT, payload)
    if score <= -25:
        return AnalyzerResult(CODE, "sell", min(90.0, 50 + abs(score)), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", abs(score), WEIGHT_DEFAULT, payload)


class SupplyDemandAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
