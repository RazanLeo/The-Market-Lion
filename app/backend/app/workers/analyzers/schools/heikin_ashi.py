"""Heikin Ashi candles — trend persistence & reversal detection.

Formulas:
  HA_close[i] = (open[i] + high[i] + low[i] + close[i]) / 4
  HA_open[i]  = (HA_open[i-1] + HA_close[i-1]) / 2  (HA_open[0] = (open[0]+close[0])/2)
  HA_high[i]  = max(high[i], HA_open[i], HA_close[i])
  HA_low[i]   = min(low[i],  HA_open[i], HA_close[i])

Reading rules:
  • Strong up: green HA candle with NO lower shadow.
  • Strong down: red HA candle with NO upper shadow.
  • Doji HA (small body, both shadows): potential reversal.
  • Streak: count of consecutive same-color candles.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "heikin_ashi"
WEIGHT_DEFAULT = 0.85


def _build_ha(df: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c = df["o"], df["h"], df["l"], df["c"]
    ha_close = (o + h + l + c) / 4
    ha_open = pd.Series(index=df.index, dtype=float)
    ha_open.iloc[0] = (o.iloc[0] + c.iloc[0]) / 2
    for i in range(1, len(df)):
        ha_open.iloc[i] = (ha_open.iloc[i - 1] + ha_close.iloc[i - 1]) / 2
    ha_high = pd.concat([h, ha_open, ha_close], axis=1).max(axis=1)
    ha_low = pd.concat([l, ha_open, ha_close], axis=1).min(axis=1)
    return pd.DataFrame({"o": ha_open, "h": ha_high, "l": ha_low, "c": ha_close}, index=df.index)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    ha = _build_ha(df)
    last = ha.iloc[-1]
    body = float(last["c"] - last["o"])
    upper_shadow = float(last["h"] - max(last["c"], last["o"]))
    lower_shadow = float(min(last["c"], last["o"]) - last["l"])
    full_range = float(last["h"] - last["l"]) or 1e-9

    bullish = body > 0
    no_lower = lower_shadow / full_range < 0.05
    no_upper = upper_shadow / full_range < 0.05
    strong_up = bullish and no_lower
    strong_dn = (not bullish) and no_upper
    is_doji = abs(body) / full_range < 0.10 and lower_shadow / full_range > 0.25 and upper_shadow / full_range > 0.25

    # Streak
    streak = 1
    cur_dir = bullish
    for i in range(2, min(len(ha), 20)):
        prev = ha.iloc[-i]
        prev_bull = prev["c"] > prev["o"]
        if prev_bull == cur_dir:
            streak += 1
        else:
            break

    payload = {
        "ha_open": round(float(last["o"]), 5),
        "ha_close": round(float(last["c"]), 5),
        "body_to_range_pct": round(abs(body) / full_range * 100, 1),
        "upper_shadow_pct": round(upper_shadow / full_range * 100, 1),
        "lower_shadow_pct": round(lower_shadow / full_range * 100, 1),
        "strong_up": strong_up, "strong_down": strong_dn,
        "doji": is_doji, "streak": streak,
        "current_direction": "up" if bullish else "down",
    }

    if is_doji:
        # potential reversal — opposite of current trend
        if bullish: return AnalyzerResult(CODE, "sell", 60.0, WEIGHT_DEFAULT, payload)
        return AnalyzerResult(CODE, "buy", 60.0, WEIGHT_DEFAULT, payload)
    if strong_up:
        return AnalyzerResult(CODE, "buy", min(85.0, 45 + streak * 5), WEIGHT_DEFAULT, payload)
    if strong_dn:
        return AnalyzerResult(CODE, "sell", min(85.0, 45 + streak * 5), WEIGHT_DEFAULT, payload)
    if bullish and streak >= 3: return AnalyzerResult(CODE, "buy", 55.0, WEIGHT_DEFAULT, payload)
    if (not bullish) and streak >= 3: return AnalyzerResult(CODE, "sell", 55.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class HeikinAshiAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
