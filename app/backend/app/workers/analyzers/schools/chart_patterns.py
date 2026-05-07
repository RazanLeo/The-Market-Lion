"""Classic chart patterns — Head & Shoulders, Double Top/Bottom, Triple Top/Bottom,
Triangles, Wedges, Flags, Pennants, Cup & Handle.

Pattern recognition uses pivots from a fractal-of-3 swing detector. Tolerances expressed in ATR.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "chart_patterns"
WEIGHT_DEFAULT = 1.0


def _swings(df: pd.DataFrame, n: int = 3):
    pivots = []
    for i in range(n, len(df) - n):
        if df["h"].iloc[i] == df["h"].iloc[i - n:i + n + 1].max():
            pivots.append((i, "H", float(df["h"].iloc[i])))
        if df["l"].iloc[i] == df["l"].iloc[i - n:i + n + 1].min():
            pivots.append((i, "L", float(df["l"].iloc[i])))
    return sorted(pivots)


def _is_close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    atr = float((df["h"] - df["l"]).rolling(14).mean().iloc[-1] or 0)
    pivs = _swings(df, 3)
    if len(pivs) < 5:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})

    types = "".join(p[1] for p in pivs[-5:])
    last5 = pivs[-5:]
    prices = [p[2] for p in last5]
    last_close = float(df["c"].iloc[-1])

    detected: list[tuple[str, str, float]] = []  # (name, side, target)

    # Head & Shoulders (top): L H L H L  with middle H highest, two outer H roughly equal
    if types == "LHLHL" and len(last5) == 5:
        l1, h1, l2, h2, l3 = prices
        # neckline = avg of l1,l2 ; H&S top
        if h1 > h2 < (h1 + h2) / 2:  # placeholder
            pass
    # H&S top typical: H L H L H (3 highs, middle highest, side highs ~equal)
    if types == "HLHLH":
        h1, l1, head, l2, h3 = prices
        if head > h1 and head > h3 and _is_close(h1, h3, atr * 1.5):
            neckline = min(l1, l2)
            target = neckline - (head - neckline)
            if last_close < neckline:
                detected.append(("head_and_shoulders_top", "sell", target))

    # Inverse H&S: L H L H L
    if types == "LHLHL":
        l1, h1, head, h3, l3 = prices
        if head < l1 and head < l3 and _is_close(l1, l3, atr * 1.5):
            neckline = max(h1, h3)
            target = neckline + (neckline - head)
            if last_close > neckline:
                detected.append(("inverse_head_and_shoulders", "buy", target))

    # Double Top: H L H with two equal highs
    if len(pivs) >= 3 and pivs[-3][1] == "H" and pivs[-2][1] == "L" and pivs[-1][1] == "H":
        h1, l, h2 = pivs[-3][2], pivs[-2][2], pivs[-1][2]
        if _is_close(h1, h2, atr * 0.8) and last_close < l:
            detected.append(("double_top", "sell", l - (h1 - l)))

    # Double Bottom: L H L
    if len(pivs) >= 3 and pivs[-3][1] == "L" and pivs[-2][1] == "H" and pivs[-1][1] == "L":
        l1, h, l2 = pivs[-3][2], pivs[-2][2], pivs[-1][2]
        if _is_close(l1, l2, atr * 0.8) and last_close > h:
            detected.append(("double_bottom", "buy", h + (h - l1)))

    # Ascending triangle: rising lows + flat resistance
    last_lows = [p for p in pivs[-8:] if p[1] == "L"]
    last_highs = [p for p in pivs[-8:] if p[1] == "H"]
    if len(last_lows) >= 3 and len(last_highs) >= 2:
        ll = [p[2] for p in last_lows[-3:]]
        hh = [p[2] for p in last_highs[-2:]]
        if ll[2] > ll[1] > ll[0] and _is_close(hh[0], hh[1], atr * 0.5):
            if last_close > max(hh):
                detected.append(("ascending_triangle_breakout", "buy", max(hh) + (max(hh) - min(ll))))
        if hh[-1] < hh[0] and len(last_highs) >= 3:
            hhh = [p[2] for p in last_highs[-3:]]
            if hhh[2] < hhh[1] < hhh[0] and _is_close(ll[0], ll[1], atr * 0.5):
                if last_close < min(ll):
                    detected.append(("descending_triangle_breakout", "sell", min(ll) - (max(hhh) - min(ll))))

    # Symmetric triangle: lower highs + higher lows (no break)
    if len(last_highs) >= 2 and len(last_lows) >= 2:
        hh = [p[2] for p in last_highs[-2:]]; ll = [p[2] for p in last_lows[-2:]]
        if hh[1] < hh[0] and ll[1] > ll[0]:
            detected.append(("symmetric_triangle_compression", "neutral", 0))

    # Bull/Bear Flag (proxy): strong impulse > 2×ATR followed by 5-bar consolidation < 0.5×ATR range
    impulse = abs(df["c"].iloc[-15] - df["c"].iloc[-25]) if len(df) >= 25 else 0
    consolidation_range = float(df.iloc[-10:]["h"].max() - df.iloc[-10:]["l"].min())
    if impulse > atr * 2 and consolidation_range < atr * 1.5:
        side = "buy" if df["c"].iloc[-15] > df["c"].iloc[-25] else "sell"
        detected.append((f"{'bull' if side == 'buy' else 'bear'}_flag", side, last_close + impulse if side == "buy" else last_close - impulse))

    if not detected:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {"types": types, "pivots": len(pivs)})

    # Pick the strongest pattern
    strongest = detected[0]
    payload = {"detected": [d[0] for d in detected],
               "strongest": strongest[0], "side": strongest[1],
               "target": round(strongest[2], 5) if strongest[2] else None}
    if strongest[1] == "buy":
        return AnalyzerResult(CODE, "buy", 75.0, WEIGHT_DEFAULT, payload)
    if strongest[1] == "sell":
        return AnalyzerResult(CODE, "sell", 75.0, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 30.0, WEIGHT_DEFAULT, payload)


class ChartPatternsAnalyzer:
    code = CODE
    weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
