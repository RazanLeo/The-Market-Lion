"""Market Breadth — A/D ratio and range-expansion analysis from a single OHLCV.

  • A/D ratio over last 20 bars: up_bars / down_bars.
  • Advance Volume Ratio: up_vol / down_vol.
  • Up-range expansion: avg(up_bar_range) > avg(down_bar_range)?
A bullish "Breadth Thrust" = A/D ratio > 1.5 AND adv_vol_ratio > 1.5 within last 10 bars.
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "market_breadth"
WEIGHT_DEFAULT = 0.85


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    win = df.iloc[-20:]
    diff = win["c"].diff()
    up = (diff > 0); dn = (diff < 0)
    n_up = int(up.sum()); n_dn = int(dn.sum()) or 1
    ad_ratio = n_up / n_dn
    v_up = float(win["v"][up].sum()); v_dn = float(win["v"][dn].sum()) or 1
    av_ratio = v_up / v_dn
    rng_up = float((win["h"][up] - win["l"][up]).mean() or 0)
    rng_dn = float((win["h"][dn] - win["l"][dn]).mean() or 0)
    range_exp_up = rng_up > rng_dn * 1.1
    range_exp_dn = rng_dn > rng_up * 1.1
    win10 = df.iloc[-10:]
    diff10 = win10["c"].diff()
    up10 = (diff10 > 0); dn10 = (diff10 < 0)
    n_up10 = int(up10.sum()); n_dn10 = int(dn10.sum()) or 1
    ad10 = n_up10 / n_dn10
    v_up10 = float(win10["v"][up10].sum()); v_dn10 = float(win10["v"][dn10].sum()) or 1
    av10 = v_up10 / v_dn10
    breadth_thrust_up = ad10 > 1.5 and av10 > 1.5
    breadth_thrust_dn = ad10 < 0.67 and av10 < 0.67
    payload = {"ad_ratio_20": round(ad_ratio, 2), "adv_vol_ratio_20": round(av_ratio, 2),
               "range_exp_up": range_exp_up, "range_exp_down": range_exp_dn,
               "breadth_thrust_up": breadth_thrust_up, "breadth_thrust_down": breadth_thrust_dn}
    if breadth_thrust_up: return AnalyzerResult(CODE, "buy", 80, WEIGHT_DEFAULT, payload)
    if breadth_thrust_dn: return AnalyzerResult(CODE, "sell", 80, WEIGHT_DEFAULT, payload)
    if ad_ratio > 1.3 and av_ratio > 1.2: return AnalyzerResult(CODE, "buy", 50, WEIGHT_DEFAULT, payload)
    if ad_ratio < 0.77 and av_ratio < 0.83: return AnalyzerResult(CODE, "sell", 50, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class MarketBreadthAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
