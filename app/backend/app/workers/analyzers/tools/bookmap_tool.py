"""Bookmap Tool — heatmap layers from BSL/SSL + Iceberg + Absorption events.

Renders rectangles at price levels with high resting liquidity proxy:
  - BSL clusters (equal highs) at price = liquidity above
  - SSL clusters (equal lows) at price = liquidity below
  - Absorption: tight-range high-volume bars
Each drawing uses opacity proportional to event count.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "bookmap_tool"
WEIGHT_DEFAULT = 1.0


def _atr(df, n=14):
    h, l, c = df["h"], df["l"], df["c"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] or 0)


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    atr = _atr(df)
    if atr <= 0:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"drawings": []})
    tol = atr * 0.2
    win = df.iloc[-60:]
    eq_highs: dict = {}; eq_lows: dict = {}
    for i in range(len(win)):
        h = round(float(win["h"].iloc[i]) / tol) * tol
        l = round(float(win["l"].iloc[i]) / tol) * tol
        eq_highs[h] = eq_highs.get(h, 0) + 1
        eq_lows[l] = eq_lows.get(l, 0) + 1
    bsl = sorted([(p, n) for p, n in eq_highs.items() if n >= 2], key=lambda x: -x[1])[:3]
    ssl = sorted([(p, n) for p, n in eq_lows.items() if n >= 2], key=lambda x: -x[1])[:3]
    drawings = []
    for p, n in bsl:
        opa = min(0.5, 0.15 + n * 0.05)
        drawings.append({"type": "rect", "x1": str(win.index[0]), "y1": p - tol * 0.3,
                         "x2": str(df.index[-1]), "y2": p + tol * 0.3,
                         "color": f"rgba(220,38,38,{opa:.2f})", "label": f"BSL×{n}"})
    for p, n in ssl:
        opa = min(0.5, 0.15 + n * 0.05)
        drawings.append({"type": "rect", "x1": str(win.index[0]), "y1": p - tol * 0.3,
                         "x2": str(df.index[-1]), "y2": p + tol * 0.3,
                         "color": f"rgba(34,197,94,{opa:.2f})", "label": f"SSL×{n}"})
    vol_avg = float(df["v"].rolling(20).mean().iloc[-1] or 0)
    body = abs(float(df["c"].iloc[-1]) - float(df["o"].iloc[-1]))
    is_absorption = (float(df["v"].iloc[-1]) > 2 * vol_avg) and (body < atr * 0.3) if vol_avg > 0 else False
    if is_absorption:
        drawings.append({"type": "marker", "x": str(df.index[-1]),
                         "y": float(df["c"].iloc[-1]),
                         "shape": "diamond", "color": "#C9A227", "label": "Absorption"})
    last_c = float(df["c"].iloc[-1])
    bias_buy = bool(ssl and abs(last_c - ssl[0][0]) < tol * 1.5)
    bias_sell = bool(bsl and abs(bsl[0][0] - last_c) < tol * 1.5)
    payload = {"drawings": drawings, "bsl_count": len(bsl), "ssl_count": len(ssl),
               "absorption_bar": is_absorption,
               "nearest_bsl": bsl[0] if bsl else None,
               "nearest_ssl": ssl[0] if ssl else None}
    if bias_buy:
        return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if bias_sell:
        return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class BookmapToolTool:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
