"""Lion Signals Tool — master renderer for Buy/Sell Cub & Lion markers.

Aggregates 4 signal types into colored markers on chart:
  Buy Cub  → small green triangle below bar
  Sell Cub → small red triangle above bar
  Buy Lion → large gold star below bar (institutional grade)
  Sell Lion→ large gold star above bar
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "lion_signals_tool"
WEIGHT_DEFAULT = 1.2


def _rsi(c, n=14):
    diff = c.diff()
    up = diff.clip(lower=0); dn = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / (ad + 1e-9))


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    rsi = _rsi(df["c"]).iloc[-1]
    atr = float(_atr(df).iloc[-1] or 0)
    last_c = float(df["c"].iloc[-1]); prev_c = float(df["c"].iloc[-2])
    swing_low = float(df["l"].iloc[-20:].min())
    swing_high = float(df["h"].iloc[-20:].max())
    last_h = float(df["h"].iloc[-1]); last_l = float(df["l"].iloc[-1])
    ts_last = str(df.index[-1])
    ema20 = df["c"].ewm(span=20, adjust=False).mean()
    above_ema = last_c > float(ema20.iloc[-1])
    vol_avg = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    vol_ok = float(df["v"].iloc[-1]) > 1.5 * vol_avg if vol_avg > 0 else False
    near_low = (last_c - swing_low) <= 0.6 * atr
    near_high = (swing_high - last_c) <= 0.6 * atr
    buy_cub = bool(rsi < 35 and last_c > prev_c and near_low)
    sell_cub = bool(rsi > 65 and last_c < prev_c and near_high)
    bos_up = last_c > swing_high
    bos_dn = last_c < swing_low
    buy_lion = bool(bos_up and above_ema and vol_ok and 35 < rsi < 70)
    sell_lion = bool(bos_dn and (not above_ema) and vol_ok and 30 < rsi < 65)
    drawings = []
    if buy_cub:
        drawings.append({"type": "marker", "x": ts_last, "y": last_l,
                         "shape": "triangle_up", "color": "#16a34a", "size": "small",
                         "label": "Buy Cub"})
    if sell_cub:
        drawings.append({"type": "marker", "x": ts_last, "y": last_h,
                         "shape": "triangle_down", "color": "#dc2626", "size": "small",
                         "label": "Sell Cub"})
    if buy_lion:
        drawings.append({"type": "marker", "x": ts_last, "y": last_l,
                         "shape": "star", "color": "#C9A227", "size": "large",
                         "label": "BUY LION"})
    if sell_lion:
        drawings.append({"type": "marker", "x": ts_last, "y": last_h,
                         "shape": "star", "color": "#C9A227", "size": "large",
                         "label": "SELL LION"})
    payload = {"drawings": drawings, "buy_cub": buy_cub, "sell_cub": sell_cub,
               "buy_lion": buy_lion, "sell_lion": sell_lion, "rsi": round(float(rsi), 1)}
    if buy_lion:
        return AnalyzerResult(CODE, "buy", 90, WEIGHT_DEFAULT, payload)
    if sell_lion:
        return AnalyzerResult(CODE, "sell", 90, WEIGHT_DEFAULT, payload)
    if buy_cub:
        return AnalyzerResult(CODE, "buy", 70, WEIGHT_DEFAULT, payload)
    if sell_cub:
        return AnalyzerResult(CODE, "sell", 70, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class LionSignalsToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
