"""Seasonality School — day-of-week and time-of-month bias.

Compute average return per weekday over last 200 bars; identify the strongest day.
Same for day-of-month groups (first/middle/last third).
"""
from __future__ import annotations
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "seasonality_school"
WEIGHT_DEFAULT = 0.6


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 200 or not isinstance(df.index, pd.DatetimeIndex):
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    ret = df["c"].pct_change()
    last_ts = df.index[-1]
    cur_dow = last_ts.dayofweek
    cur_dom = last_ts.day
    dom_third = "early" if cur_dom <= 10 else "mid" if cur_dom <= 20 else "late"
    win = df.iloc[-200:]
    wret = ret.iloc[-200:]
    dow_means = wret.groupby(win.index.dayofweek).mean()
    cur_dow_mean = float(dow_means.get(cur_dow, 0))
    bins = pd.cut(win.index.day, [0, 10, 20, 31], labels=["early", "mid", "late"], include_lowest=True)
    dom_means = wret.groupby(bins, observed=False).mean()
    cur_dom_mean = float(dom_means.get(dom_third, 0))
    bias_score = (cur_dow_mean + cur_dom_mean) * 1000  # tiny pct → scale up
    payload = {"weekday": int(cur_dow), "weekday_avg_return_pct": round(cur_dow_mean * 100, 4),
               "month_third": dom_third, "month_third_avg_return_pct": round(cur_dom_mean * 100, 4),
               "bias_score": round(bias_score, 2)}
    if bias_score > 1.5: return AnalyzerResult(CODE, "buy", min(60.0, 35 + bias_score * 5), WEIGHT_DEFAULT, payload)
    if bias_score < -1.5: return AnalyzerResult(CODE, "sell", min(60.0, 35 + abs(bias_score) * 5), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class SeasonalitySchoolAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
