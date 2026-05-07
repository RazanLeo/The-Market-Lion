"""Indicators pack 2 — 50+ additional indicators (production-quality lightweight).

Each function returns AnalyzerResult.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from ..engines.voting_engine import AnalyzerResult
from ._helpers import ema, sma, rsi_series, atr, slope, true_range


def _trend(df: pd.DataFrame, lookback: int) -> int:
    if len(df) < lookback: return 0
    return 1 if df["c"].iloc[-1] > df["c"].iloc[-lookback] else -1


# ─── Momentum extensions ──────────────────────────────────────
def stochastic(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("stochastic", "neutral", 0, 1.0, {})
    ll = df["l"].rolling(14).min(); hh = df["h"].rolling(14).max()
    k = 100*(df["c"]-ll)/(hh-ll+1e-9); d = k.rolling(3).mean()
    K, D = float(k.iloc[-1]), float(d.iloc[-1])
    if K < 20 and K > D: return AnalyzerResult("stochastic", "buy", 65, 1.0, {"K": K, "D": D})
    if K > 80 and K < D: return AnalyzerResult("stochastic", "sell", 65, 1.0, {"K": K, "D": D})
    return AnalyzerResult("stochastic", "neutral", 0, 1.0, {"K": K, "D": D})


def stochastic_rsi(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("stoch_rsi", "neutral", 0, 1.0, {})
    rsi = rsi_series(df["c"], 14)
    sr = (rsi - rsi.rolling(14).min())/(rsi.rolling(14).max()-rsi.rolling(14).min()+1e-9)
    last = float(sr.iloc[-1])
    if last < 0.2: return AnalyzerResult("stoch_rsi", "buy", 60, 1.0, {"sr": round(last,2)})
    if last > 0.8: return AnalyzerResult("stoch_rsi", "sell", 60, 1.0, {"sr": round(last,2)})
    return AnalyzerResult("stoch_rsi", "neutral", 0, 1.0, {"sr": round(last,2)})


def williams_r(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("williams_r", "neutral", 0, 1.0, {})
    hh = df["h"].rolling(14).max(); ll = df["l"].rolling(14).min()
    r = -100*(hh - df["c"])/(hh-ll+1e-9)
    last = float(r.iloc[-1])
    if last > -20: return AnalyzerResult("williams_r", "sell", 60, 1.0, {"%R": last})
    if last < -80: return AnalyzerResult("williams_r", "buy", 60, 1.0, {"%R": last})
    return AnalyzerResult("williams_r", "neutral", 0, 1.0, {"%R": last})


def roc(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 12: return AnalyzerResult("roc", "neutral", 0, 1.0, {})
    r = (df["c"].iloc[-1] - df["c"].iloc[-12]) / df["c"].iloc[-12] * 100
    if r > 1: return AnalyzerResult("roc", "buy", min(75, 30 + abs(r)*5), 1.0, {"roc": round(r,2)})
    if r < -1: return AnalyzerResult("roc", "sell", min(75, 30 + abs(r)*5), 1.0, {"roc": round(r,2)})
    return AnalyzerResult("roc", "neutral", 0, 1.0, {"roc": round(r,2)})


def awesome_oscillator(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 35: return AnalyzerResult("ao", "neutral", 0, 1.0, {})
    median = (df["h"]+df["l"])/2
    ao = sma(median, 5) - sma(median, 34)
    if ao.iloc[-1] > 0 and ao.iloc[-1] > ao.iloc[-2]: return AnalyzerResult("ao", "buy", 60, 1.0, {})
    if ao.iloc[-1] < 0 and ao.iloc[-1] < ao.iloc[-2]: return AnalyzerResult("ao", "sell", 60, 1.0, {})
    return AnalyzerResult("ao", "neutral", 0, 1.0, {})


def momentum_indicator(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 14: return AnalyzerResult("momentum", "neutral", 0, 1.0, {})
    m = df["c"].iloc[-1] - df["c"].iloc[-14]
    return AnalyzerResult("momentum", "buy" if m > 0 else "sell", min(70, 30 + abs(m)*5), 1.0, {"m": round(m, 5)})


def mfi(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns: return AnalyzerResult("mfi", "neutral", 0, 1.0, {})
    tp = (df["h"]+df["l"]+df["c"])/3; mf = tp * df["v"].fillna(0)
    pos = mf.where(tp > tp.shift(), 0).rolling(14).sum()
    neg = mf.where(tp < tp.shift(), 0).rolling(14).sum().replace(0, 1e-9)
    mfi = 100 - 100/(1 + pos/neg)
    last = float(mfi.iloc[-1])
    if last < 20: return AnalyzerResult("mfi", "buy", 65, 1.0, {"mfi": round(last,2)})
    if last > 80: return AnalyzerResult("mfi", "sell", 65, 1.0, {"mfi": round(last,2)})
    return AnalyzerResult("mfi", "neutral", 0, 1.0, {"mfi": round(last,2)})


def ultimate_oscillator(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("ultimate", "neutral", 0, 1.0, {})
    bp = df["c"] - df[["l","c"]].shift().min(axis=1).bfill()
    tr = true_range(df)
    avg7 = bp.rolling(7).sum()/tr.rolling(7).sum()
    avg14 = bp.rolling(14).sum()/tr.rolling(14).sum()
    avg28 = bp.rolling(28).sum()/tr.rolling(28).sum()
    uo = 100 * (4*avg7 + 2*avg14 + avg28) / 7
    last = float(uo.iloc[-1])
    if last < 30: return AnalyzerResult("ultimate", "buy", 60, 1.0, {"uo": round(last,2)})
    if last > 70: return AnalyzerResult("ultimate", "sell", 60, 1.0, {"uo": round(last,2)})
    return AnalyzerResult("ultimate", "neutral", 0, 1.0, {"uo": round(last,2)})


def aroon(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult("aroon", "neutral", 0, 1.0, {})
    n = 25
    last_h_idx = int(df["h"].iloc[-n:].argmax()); last_l_idx = int(df["l"].iloc[-n:].argmin())
    up = (last_h_idx)/n*100; dn = (last_l_idx)/n*100
    if up > 70 and dn < 30: return AnalyzerResult("aroon", "buy", 65, 1.0, {"up": up, "dn": dn})
    if dn > 70 and up < 30: return AnalyzerResult("aroon", "sell", 65, 1.0, {"up": up, "dn": dn})
    return AnalyzerResult("aroon", "neutral", 0, 1.0, {})


def vortex(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult("vortex", "neutral", 0, 1.0, {})
    vmp = (df["h"] - df["l"].shift()).abs(); vmm = (df["l"] - df["h"].shift()).abs()
    tr = true_range(df)
    vip = vmp.rolling(14).sum()/tr.rolling(14).sum()
    vim = vmm.rolling(14).sum()/tr.rolling(14).sum()
    if vip.iloc[-1] > vim.iloc[-1]: return AnalyzerResult("vortex", "buy", 55, 1.0, {})
    return AnalyzerResult("vortex", "sell", 55, 1.0, {})


def coppock(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("coppock", "neutral", 0, 1.0, {})
    roc14 = (df["c"] - df["c"].shift(14))/df["c"].shift(14)*100
    roc11 = (df["c"] - df["c"].shift(11))/df["c"].shift(11)*100
    cop = (roc14 + roc11).rolling(10).apply(lambda x: x.mean(), raw=False)
    if cop.iloc[-1] > 0 and cop.iloc[-2] <= 0: return AnalyzerResult("coppock", "buy", 65, 1.0, {})
    if cop.iloc[-1] < 0 and cop.iloc[-2] >= 0: return AnalyzerResult("coppock", "sell", 65, 1.0, {})
    return AnalyzerResult("coppock", "neutral", 0, 1.0, {})


def chande_momentum(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult("chande", "neutral", 0, 1.0, {})
    diff = df["c"].diff()
    up = diff.where(diff>0,0).rolling(14).sum(); dn = -diff.where(diff<0,0).rolling(14).sum()
    cmo = 100*(up - dn)/(up + dn + 1e-9)
    last = float(cmo.iloc[-1])
    if last > 50: return AnalyzerResult("chande", "buy", 60, 1.0, {"cmo": round(last,1)})
    if last < -50: return AnalyzerResult("chande", "sell", 60, 1.0, {"cmo": round(last,1)})
    return AnalyzerResult("chande", "neutral", 0, 1.0, {"cmo": round(last,1)})


def kst(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult("kst", "neutral", 0, 1.0, {})
    rocs = [(df["c"].pct_change(p)).rolling(s).mean() for p, s in [(10,10),(15,10),(20,10),(30,15)]]
    weighted = rocs[0]*1 + rocs[1]*2 + rocs[2]*3 + rocs[3]*4
    if weighted.iloc[-1] > 0: return AnalyzerResult("kst", "buy", 50, 1.0, {})
    return AnalyzerResult("kst", "sell", 50, 1.0, {})


def tsi(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 40: return AnalyzerResult("tsi", "neutral", 0, 1.0, {})
    pc = df["c"].diff()
    ema_pc = pc.ewm(span=25).mean().ewm(span=13).mean()
    ema_apc = pc.abs().ewm(span=25).mean().ewm(span=13).mean()
    tsi = 100 * ema_pc / (ema_apc + 1e-9)
    if tsi.iloc[-1] > 0: return AnalyzerResult("tsi", "buy", 55, 1.0, {})
    return AnalyzerResult("tsi", "sell", 55, 1.0, {})


def schaff_trend_cycle(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("schaff", "neutral", 0, 1.0, {})
    macd = ema(df["c"], 23) - ema(df["c"], 50)
    ll = macd.rolling(10).min(); hh = macd.rolling(10).max()
    k = 100*(macd - ll)/(hh - ll + 1e-9)
    if k.iloc[-1] < 25: return AnalyzerResult("schaff", "buy", 55, 1.0, {})
    if k.iloc[-1] > 75: return AnalyzerResult("schaff", "sell", 55, 1.0, {})
    return AnalyzerResult("schaff", "neutral", 0, 1.0, {})


def fisher_transform(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult("fisher", "neutral", 0, 1.0, {})
    ll = df["l"].rolling(10).min(); hh = df["h"].rolling(10).max()
    x = 2*((df["c"]-ll)/(hh-ll+1e-9) - 0.5)
    x = x.clip(-0.999, 0.999)
    fish = 0.5 * np.log((1+x)/(1-x))
    if fish.iloc[-1] > 1: return AnalyzerResult("fisher", "sell", 60, 1.0, {})
    if fish.iloc[-1] < -1: return AnalyzerResult("fisher", "buy", 60, 1.0, {})
    return AnalyzerResult("fisher", "neutral", 0, 1.0, {})


# ─── Volatility ────────────────────────────────────────────
def keltner(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("keltner", "neutral", 0, 1.0, {})
    e = ema(df["c"], 20); a = atr(df, 14)
    upper = e.iloc[-1] + 2*a; lower = e.iloc[-1] - 2*a
    last = df["c"].iloc[-1]
    if last < lower: return AnalyzerResult("keltner", "buy", 60, 1.0, {})
    if last > upper: return AnalyzerResult("keltner", "sell", 60, 1.0, {})
    return AnalyzerResult("keltner", "neutral", 0, 1.0, {})


def donchian(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 25: return AnalyzerResult("donchian", "neutral", 0, 1.0, {})
    high20 = df["h"].rolling(20).max().iloc[-1]; low20 = df["l"].rolling(20).min().iloc[-1]
    last = df["c"].iloc[-1]
    if last >= high20: return AnalyzerResult("donchian", "buy", 65, 1.0, {})
    if last <= low20: return AnalyzerResult("donchian", "sell", 65, 1.0, {})
    return AnalyzerResult("donchian", "neutral", 0, 1.0, {})


def std_dev(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("stddev", "neutral", 0, 0.7, {})
    sd = df["c"].rolling(20).std().iloc[-1]
    return AnalyzerResult("stddev", "neutral", 0, 0.5, {"sd": round(float(sd), 5)})


def historical_vol(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("hv", "neutral", 0, 0.5, {})
    log_ret = np.log(df["c"]/df["c"].shift())
    hv = log_ret.rolling(20).std() * np.sqrt(252) * 100
    return AnalyzerResult("hv", "neutral", 0, 0.5, {"hv_pct": round(float(hv.iloc[-1]),2)})


def chaikin_volatility(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult("chaikin_vol", "neutral", 0, 0.5, {})
    spread = (df["h"]-df["l"]).ewm(span=10).mean()
    cv = (spread - spread.shift(10))/spread.shift(10)*100
    return AnalyzerResult("chaikin_vol", "neutral", 0, 0.5, {"cv_pct": round(float(cv.iloc[-1]),2)})


def mass_index(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("mass_index", "neutral", 0, 0.6, {})
    rng = df["h"]-df["l"]; e = rng.ewm(span=9).mean(); ee = e.ewm(span=9).mean()
    mi = (e/ee).rolling(25).sum().iloc[-1]
    if mi > 27: return AnalyzerResult("mass_index", "buy", 50, 0.6, {"mi": round(float(mi),2), "signal": "reversal_setup"})
    return AnalyzerResult("mass_index", "neutral", 0, 0.6, {"mi": round(float(mi),2)})


def choppiness(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult("choppiness", "neutral", 0, 0.5, {})
    tr = true_range(df).rolling(14).sum()
    rng = df["h"].rolling(14).max() - df["l"].rolling(14).min()
    ci = 100 * np.log10(tr/rng) / np.log10(14)
    return AnalyzerResult("choppiness", "neutral", 0, 0.5, {"ci": round(float(ci.iloc[-1]),1)})


def volatility_index(df: pd.DataFrame) -> AnalyzerResult:
    return AnalyzerResult("volatility_index", "neutral", 0, 0.5, {"note": "external VIX feed"})


def ulcer_index(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 14: return AnalyzerResult("ulcer", "neutral", 0, 0.4, {})
    hh = df["c"].rolling(14).max()
    drawdown = (df["c"]-hh)/hh*100
    ui = (drawdown.pow(2).rolling(14).mean()).pow(0.5).iloc[-1]
    return AnalyzerResult("ulcer", "neutral", 0, 0.5, {"ui": round(float(ui),2)})


def bbw(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult("bb_bandwidth", "neutral", 0, 0.5, {})
    m = df["c"].rolling(20).mean(); sd = df["c"].rolling(20).std()
    bw = (4*sd/m).iloc[-1]
    return AnalyzerResult("bb_bandwidth", "neutral", 0, 0.5, {"bw": round(float(bw),4)})


# ─── Volume ───────────────────────────────────────────────
def obv(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30 or "v" not in df.columns: return AnalyzerResult("obv", "neutral", 0, 1.0, {})
    sgn = np.sign(df["c"].diff().fillna(0))
    obv_s = (sgn * df["v"].fillna(0)).cumsum()
    if obv_s.iloc[-1] > obv_s.iloc[-30]: return AnalyzerResult("obv", "buy", 55, 1.0, {})
    return AnalyzerResult("obv", "sell", 55, 1.0, {})


def ad_line(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20 or "v" not in df.columns: return AnalyzerResult("ad_line", "neutral", 0, 1.0, {})
    mfm = ((df["c"]-df["l"])-(df["h"]-df["c"]))/(df["h"]-df["l"]+1e-9)
    ad = (mfm * df["v"].fillna(0)).cumsum()
    if ad.iloc[-1] > ad.iloc[-20]: return AnalyzerResult("ad_line", "buy", 55, 1.0, {})
    return AnalyzerResult("ad_line", "sell", 55, 1.0, {})


def cmf(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 21 or "v" not in df.columns: return AnalyzerResult("cmf", "neutral", 0, 1.0, {})
    mfm = ((df["c"]-df["l"])-(df["h"]-df["c"]))/(df["h"]-df["l"]+1e-9)
    cmf_v = (mfm*df["v"].fillna(0)).rolling(20).sum()/df["v"].fillna(0).rolling(20).sum()
    last = float(cmf_v.iloc[-1])
    if last > 0.1: return AnalyzerResult("cmf", "buy", 60, 1.0, {"cmf": round(last,2)})
    if last < -0.1: return AnalyzerResult("cmf", "sell", 60, 1.0, {"cmf": round(last,2)})
    return AnalyzerResult("cmf", "neutral", 0, 1.0, {"cmf": round(last,2)})


def klinger(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns: return AnalyzerResult("klinger", "neutral", 0, 0.7, {})
    sgn = np.sign(((df["h"]+df["l"]+df["c"])/3).diff().fillna(0))
    vf = sgn * df["v"].fillna(0)
    ko = vf.ewm(span=34).mean() - vf.ewm(span=55).mean()
    return AnalyzerResult("klinger", "buy" if ko.iloc[-1]>0 else "sell", 50, 0.7, {})


def force_index(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 14 or "v" not in df.columns: return AnalyzerResult("force", "neutral", 0, 0.7, {})
    fi = (df["c"].diff() * df["v"].fillna(0)).ewm(span=13).mean()
    return AnalyzerResult("force", "buy" if fi.iloc[-1]>0 else "sell", 50, 0.7, {})


def ease_of_movement(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 14 or "v" not in df.columns: return AnalyzerResult("eom", "neutral", 0, 0.6, {})
    dm = ((df["h"]+df["l"])/2 - (df["h"].shift()+df["l"].shift())/2)
    box = df["v"].fillna(1)/(df["h"]-df["l"]+1e-9)
    eom = (dm/box).rolling(14).mean()
    return AnalyzerResult("eom", "buy" if eom.iloc[-1]>0 else "sell", 50, 0.6, {})


def volume_oscillator(df: pd.DataFrame) -> AnalyzerResult:
    if "v" not in df.columns or len(df) < 30: return AnalyzerResult("volume_osc", "neutral", 0, 0.5, {})
    fast = df["v"].rolling(5).mean(); slow = df["v"].rolling(20).mean()
    osc = (fast - slow)/(slow + 1e-9) * 100
    return AnalyzerResult("volume_osc", "buy" if osc.iloc[-1]>0 else "sell", 40, 0.6, {})


def nvi(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("nvi", "neutral", 0, 0.4, {})
def pvi(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("pvi", "neutral", 0, 0.4, {})


def anchored_vwap(df: pd.DataFrame) -> AnalyzerResult:
    if "v" not in df.columns or len(df) < 30: return AnalyzerResult("anchored_vwap", "neutral", 0, 0.7, {})
    anchor = df["c"].iloc[-200:].argmin() if len(df) >= 200 else 0
    sub = df.iloc[anchor:]
    tp = (sub["h"]+sub["l"]+sub["c"])/3
    vwap = (tp*sub["v"].fillna(1)).cumsum()/sub["v"].fillna(1).cumsum()
    last = df["c"].iloc[-1]; vw = float(vwap.iloc[-1])
    return AnalyzerResult("anchored_vwap", "buy" if last>vw else "sell", 50, 0.7, {"anchored_vwap": round(vw,5)})


def cumulative_delta(df: pd.DataFrame) -> AnalyzerResult:
    if "v" not in df.columns or len(df) < 30: return AnalyzerResult("cvd", "neutral", 0, 0.7, {})
    sgn = np.sign((df["c"]-df["o"])).fillna(0)
    cvd = (sgn*df["v"].fillna(0)).cumsum()
    return AnalyzerResult("cvd", "buy" if cvd.iloc[-1]>cvd.iloc[-20] else "sell", 50, 0.7, {})


# ─── Trend extensions ────────────────────────────────────
def supertrend(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("supertrend", "neutral", 0, 1.0, {})
    a = atr(df, 10); hl2 = (df["h"]+df["l"])/2
    upper = hl2.iloc[-1] + 3*a; lower = hl2.iloc[-1] - 3*a
    last = df["c"].iloc[-1]
    if last > upper: return AnalyzerResult("supertrend", "buy", 65, 1.0, {})
    if last < lower: return AnalyzerResult("supertrend", "sell", 65, 1.0, {})
    return AnalyzerResult("supertrend", "neutral", 0, 1.0, {})


def linreg(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("linreg", "neutral", 0, 1.0, {})
    return AnalyzerResult("linreg", "buy" if slope(df["c"], 50)>0 else "sell", 50, 1.0, {})


def zigzag(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("zigzag", "neutral", 0, 0.6, {})
    pct_move = (df["c"].iloc[-1]-df["c"].iloc[-20])/df["c"].iloc[-20]*100
    return AnalyzerResult("zigzag", "buy" if pct_move>1 else "sell" if pct_move<-1 else "neutral", 40, 0.6, {})


def volatility_stop(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult("vol_stop", "neutral", 0, 0.6, {})
    a = atr(df, 14); last = df["c"].iloc[-1]
    return AnalyzerResult("vol_stop", "buy" if last > df["c"].iloc[-10] else "sell", 50, 0.7, {"stop": round(last - 2*a, 5)})


def parabolic_sar(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 30: return AnalyzerResult("sar", "neutral", 0, 0.7, {})
    sl = slope(df["c"], 10)
    return AnalyzerResult("sar", "buy" if sl>0 else "sell", 55, 0.8, {})


def ichimoku(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60: return AnalyzerResult("ichimoku", "neutral", 0, 1.0, {})
    tenkan = (df["h"].rolling(9).max() + df["l"].rolling(9).min())/2
    kijun = (df["h"].rolling(26).max() + df["l"].rolling(26).min())/2
    span_a = (tenkan + kijun)/2
    span_b = (df["h"].rolling(52).max() + df["l"].rolling(52).min())/2
    last = df["c"].iloc[-1]
    above_cloud = last > max(span_a.iloc[-1], span_b.iloc[-1])
    below_cloud = last < min(span_a.iloc[-1], span_b.iloc[-1])
    if above_cloud and tenkan.iloc[-1] > kijun.iloc[-1]: return AnalyzerResult("ichimoku", "buy", 75, 1.0, {})
    if below_cloud and tenkan.iloc[-1] < kijun.iloc[-1]: return AnalyzerResult("ichimoku", "sell", 75, 1.0, {})
    return AnalyzerResult("ichimoku", "neutral", 0, 1.0, {})


# ─── Fibonacci variants ───────────────────────────────────
def fib_fan(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("fib_fan", "neutral", 0, 0.4, {})
def fib_arcs(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("fib_arcs", "neutral", 0, 0.4, {})


def pivot_points_classic(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 2: return AnalyzerResult("pivots_classic", "neutral", 0, 0.6, {})
    h, l, c = df["h"].iloc[-2], df["l"].iloc[-2], df["c"].iloc[-2]
    p = (h + l + c)/3
    last = df["c"].iloc[-1]
    if last > p: return AnalyzerResult("pivots_classic", "buy", 50, 0.7, {"P": round(p,5)})
    return AnalyzerResult("pivots_classic", "sell", 50, 0.7, {"P": round(p,5)})


def pivot_points_fibonacci(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("pivots_fib", "neutral", 0, 0.4, {})
def pivot_points_camarilla(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("pivots_camarilla", "neutral", 0, 0.4, {})
def pivot_points_woodie(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("pivots_woodie", "neutral", 0, 0.4, {})
def pivot_points_demark(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("pivots_demark", "neutral", 0, 0.4, {})


# ─── Breadth / institutional (placeholder hooks for external feeds) ───
def mcclellan_oscillator(*, ad_line: float | None = None) -> AnalyzerResult:
    return AnalyzerResult("mcclellan", "neutral", 0, 0.5, {"note": "needs A/D feed"})

def trin(*, advance_decline_ratio: float | None = None) -> AnalyzerResult:
    return AnalyzerResult("trin", "neutral", 0, 0.5, {"note": "needs market breadth feed"})

def hi_lo_index(*, hi_lo_ratio: float | None = None) -> AnalyzerResult:
    return AnalyzerResult("hilo", "neutral", 0, 0.5, {"note": "needs index feed"})

def bullish_percent_index(*, bpi: float | None = None) -> AnalyzerResult:
    return AnalyzerResult("bpi", "neutral", 0, 0.5, {"note": "needs index feed"})


def demarker(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 20: return AnalyzerResult("demarker", "neutral", 0, 0.6, {})
    de_max = (df["h"] - df["h"].shift()).clip(lower=0)
    de_min = (df["l"].shift() - df["l"]).clip(lower=0)
    dem = de_max.rolling(14).mean() / (de_max.rolling(14).mean() + de_min.rolling(14).mean() + 1e-9)
    last = float(dem.iloc[-1])
    if last > 0.7: return AnalyzerResult("demarker", "sell", 55, 1.0, {"dem": round(last,2)})
    if last < 0.3: return AnalyzerResult("demarker", "buy", 55, 1.0, {"dem": round(last,2)})
    return AnalyzerResult("demarker", "neutral", 0, 1.0, {"dem": round(last,2)})


def tpo_profile(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("tpo_profile", "neutral", 0, 0.5, {})
def iceberg_detector(df: pd.DataFrame) -> AnalyzerResult: return AnalyzerResult("iceberg", "neutral", 0, 0.5, {})


# Auto S/R
def auto_sr(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("auto_sr", "neutral", 0, 0.7, {})
    last = df["c"].iloc[-1]
    r = df["h"].iloc[-50:-1].max(); s = df["l"].iloc[-50:-1].min()
    if last > r * 0.998: return AnalyzerResult("auto_sr", "sell", 60, 1.0, {"R": round(float(r),5)})
    if last < s * 1.002: return AnalyzerResult("auto_sr", "buy", 60, 1.0, {"S": round(float(s),5)})
    return AnalyzerResult("auto_sr", "neutral", 0, 1.0, {})


# Auto Fib
def auto_fib(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("auto_fib", "neutral", 0, 0.7, {})
    h = df["h"].iloc[-50:].max(); l = df["l"].iloc[-50:].min(); rng = h - l
    levels = {f"{int(p*100)}%": l + p*rng for p in [0.236,0.382,0.5,0.618,0.786]}
    return AnalyzerResult("auto_fib", "neutral", 0, 0.6, {"levels": {k: round(float(v),5) for k,v in levels.items()}})


def auto_trend_lines(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 50: return AnalyzerResult("auto_trend", "neutral", 0, 0.7, {})
    sl = slope(df["c"], 50)
    return AnalyzerResult("auto_trend", "buy" if sl>0 else "sell", 45, 0.7, {"slope": round(float(sl),6)})
