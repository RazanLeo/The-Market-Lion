"""Complete Technical Analysis Engine — 74 schools across 12 groups for The Market Lion.
Schools 1–29: indicators.py  |  Schools 30–74: indicators_extended.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class Vote(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


@dataclass
class SchoolResult:
    name: str
    vote: Vote
    strength: float  # 0-1
    confidence: float  # 0-1
    details: Dict[str, Any]


def safe_div(a, b, default=0.0):
    return a / b if b != 0 else default


# ─── GROUP 1: MOVING AVERAGES ────────────────────────────────────────────────

def sma(data: np.ndarray, period: int) -> np.ndarray:
    result = np.full(len(data), np.nan)
    for i in range(period - 1, len(data)):
        result[i] = np.mean(data[i - period + 1:i + 1])
    return result


def ema(data: np.ndarray, period: int) -> np.ndarray:
    result = np.full(len(data), np.nan)
    k = 2.0 / (period + 1)
    start = 0
    while start < len(data) and np.isnan(data[start]):
        start += 1
    if start >= len(data):
        return result
    result[start] = data[start]
    for i in range(start + 1, len(data)):
        if not np.isnan(data[i]):
            result[i] = data[i] * k + result[i - 1] * (1 - k)
        else:
            result[i] = result[i - 1]
    return result


def wma(data: np.ndarray, period: int) -> np.ndarray:
    result = np.full(len(data), np.nan)
    weights = np.arange(1, period + 1, dtype=float)
    for i in range(period - 1, len(data)):
        result[i] = np.dot(data[i - period + 1:i + 1], weights) / weights.sum()
    return result


def dema(data: np.ndarray, period: int) -> np.ndarray:
    e1 = ema(data, period)
    e2 = ema(e1, period)
    return 2 * e1 - e2


def tema(data: np.ndarray, period: int) -> np.ndarray:
    e1 = ema(data, period)
    e2 = ema(e1, period)
    e3 = ema(e2, period)
    return 3 * e1 - 3 * e2 + e3


def hma(data: np.ndarray, period: int) -> np.ndarray:
    half = max(1, period // 2)
    sqrt_p = max(1, int(np.sqrt(period)))
    w1 = wma(data, half)
    w2 = wma(data, period)
    diff = 2 * w1 - w2
    return wma(diff, sqrt_p)


def frama(data: np.ndarray, period: int = 16) -> np.ndarray:
    """Fractal Adaptive Moving Average."""
    result = np.full(len(data), np.nan)
    half = period // 2
    for i in range(period, len(data)):
        h1 = np.max(data[i - period + 1:i - half + 1])
        l1 = np.min(data[i - period + 1:i - half + 1])
        h2 = np.max(data[i - half + 1:i + 1])
        l2 = np.min(data[i - half + 1:i + 1])
        h3 = np.max(data[i - period + 1:i + 1])
        l3 = np.min(data[i - period + 1:i + 1])
        n1 = safe_div(h1 - l1, half)
        n2 = safe_div(h2 - l2, half)
        n3 = safe_div(h3 - l3, period)
        if n1 + n2 > 0 and n3 > 0:
            d = safe_div(np.log(n1 + n2) - np.log(n3), np.log(2))
        else:
            d = 1.0
        alpha = np.exp(-4.6 * (d - 1))
        alpha = max(0.01, min(1.0, alpha))
        if np.isnan(result[i - 1]):
            result[i] = data[i]
        else:
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
    return result


def analyze_moving_averages(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    periods_ema = [7, 10, 25]
    periods_sma = [50, 100, 200]
    price = close[-1]
    signals = []
    details = {}

    for p in periods_ema:
        val = ema(close, p)[-1]
        details[f"EMA{p}"] = round(val, 5)
        signals.append(1 if price > val else -1)

    for p in periods_sma:
        val = sma(close, p)[-1]
        details[f"SMA{p}"] = round(val, 5)
        signals.append(1 if price > val else -1)

    ema50 = ema(close, 50)
    ema200 = ema(close, 200)
    golden_cross = ema50[-1] > ema200[-1] and ema50[-2] <= ema200[-2]
    death_cross = ema50[-1] < ema200[-1] and ema50[-2] >= ema200[-2]
    details["golden_cross"] = golden_cross
    details["death_cross"] = death_cross

    score = sum(signals) / len(signals)
    if golden_cross:
        score = min(1.0, score + 0.3)
    if death_cross:
        score = max(-1.0, score - 0.3)

    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Moving Averages", vote, abs(score), min(1.0, abs(score) + 0.3), details)


# ─── GROUP 2: RSI ─────────────────────────────────────────────────────────────

def rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
    result = np.full(len(data), np.nan)
    deltas = np.diff(data)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    if len(gains) < period:
        return result
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    for i in range(period, len(data) - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = safe_div(avg_gain, avg_loss, 100)
        result[i + 1] = 100 - safe_div(100, 1 + rs)
    return result


def detect_divergence(price: np.ndarray, indicator: np.ndarray, lookback: int = 5):
    """Detect regular and hidden divergences."""
    if len(price) < lookback * 2:
        return None, None
    p_recent = price[-lookback:]
    i_recent = indicator[-lookback:]
    p_prev = price[-lookback * 2:-lookback]
    i_prev = indicator[-lookback * 2:-lookback]
    p_low_r, p_low_p = np.min(p_recent), np.min(p_prev)
    p_high_r, p_high_p = np.max(p_recent), np.max(p_prev)
    i_low_r = i_recent[np.argmin(p_recent)]
    i_low_p = i_prev[np.argmin(p_prev)]
    i_high_r = i_recent[np.argmax(p_recent)]
    i_high_p = i_prev[np.argmax(p_prev)]

    reg_bull = p_low_r < p_low_p and i_low_r > i_low_p
    reg_bear = p_high_r > p_high_p and i_high_r < i_high_p
    hid_bull = p_low_r > p_low_p and i_low_r < i_low_p
    hid_bear = p_high_r < p_high_p and i_high_r > i_high_p
    return (reg_bull, hid_bull), (reg_bear, hid_bear)


def analyze_rsi(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    rsi_vals = rsi(close, 14)
    current = rsi_vals[-1] if not np.isnan(rsi_vals[-1]) else 50
    details = {"rsi": round(current, 2)}

    bull_div, bear_div = detect_divergence(close, rsi_vals)
    details["regular_bull_div"] = bool(bull_div and bull_div[0])
    details["hidden_bull_div"] = bool(bull_div and bull_div[1])
    details["regular_bear_div"] = bool(bear_div and bear_div[0])
    details["hidden_bear_div"] = bool(bear_div and bear_div[1])

    score = 0.0
    if current < 30:
        score = (30 - current) / 30
    elif current > 70:
        score = -(current - 70) / 30
    else:
        score = (current - 50) / 50 * 0.5

    if details["regular_bull_div"]:
        score += 0.4
    if details["hidden_bull_div"]:
        score += 0.25
    if details["regular_bear_div"]:
        score -= 0.4
    if details["hidden_bear_div"]:
        score -= 0.25

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.15 else (Vote.SELL if score < -0.15 else Vote.NEUTRAL)
    return SchoolResult("RSI Pro", vote, abs(score), 0.85, details)


# ─── GROUP 3: MACD ────────────────────────────────────────────────────────────

def macd(data: np.ndarray, fast=12, slow=26, signal=9):
    ema_fast = ema(data, fast)
    ema_slow = ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def analyze_macd(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    ml, sl, hist = macd(close)
    ml_cur, sl_cur, h_cur = ml[-1], sl[-1], hist[-1]
    ml_prev, sl_prev, h_prev = ml[-2], sl[-2], hist[-2]
    details = {
        "macd_line": round(ml_cur, 5),
        "signal_line": round(sl_cur, 5),
        "histogram": round(h_cur, 5),
    }
    score = 0.0
    if ml_cur > sl_cur:
        score += 0.4
    else:
        score -= 0.4
    if ml_cur > 0:
        score += 0.2
    else:
        score -= 0.2
    if h_cur > h_prev:
        score += 0.2
    else:
        score -= 0.2
    crossover_bull = ml_prev < sl_prev and ml_cur > sl_cur
    crossover_bear = ml_prev > sl_prev and ml_cur < sl_cur
    if crossover_bull:
        score += 0.3
    if crossover_bear:
        score -= 0.3
    details["bullish_crossover"] = crossover_bull
    details["bearish_crossover"] = crossover_bear

    bull_div, bear_div = detect_divergence(close, ml)
    details["divergence_bull"] = bool(bull_div and bull_div[0])
    details["divergence_bear"] = bool(bear_div and bear_div[0])

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("MACD", vote, abs(score), 0.80, details)


# ─── GROUP 4: STOCHASTIC ─────────────────────────────────────────────────────

def stochastic(high, low, close, k_period=14, d_period=3):
    k = np.full(len(close), np.nan)
    for i in range(k_period - 1, len(close)):
        h = np.max(high[i - k_period + 1:i + 1])
        l = np.min(low[i - k_period + 1:i + 1])
        k[i] = safe_div(close[i] - l, h - l) * 100
    d = sma(k, d_period)
    return k, d


def analyze_stochastic(df: pd.DataFrame) -> SchoolResult:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    k, d = stochastic(high, low, close)
    k_cur, d_cur = k[-1], d[-1]
    k_prev, d_prev = k[-2], d[-2]
    details = {"stoch_k": round(k_cur, 2), "stoch_d": round(d_cur, 2)}
    score = 0.0
    if k_cur < 20:
        score += (20 - k_cur) / 20
    elif k_cur > 80:
        score -= (k_cur - 80) / 20
    if k_prev < d_prev and k_cur > d_cur:
        score += 0.4
    elif k_prev > d_prev and k_cur < d_cur:
        score -= 0.4
    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Stochastic", vote, abs(score), 0.75, details)


# ─── GROUP 5: BOLLINGER BANDS ─────────────────────────────────────────────────

def bollinger_bands(data: np.ndarray, period=20, std_dev=2.0):
    middle = sma(data, period)
    std = np.full(len(data), np.nan)
    for i in range(period - 1, len(data)):
        std[i] = np.std(data[i - period + 1:i + 1])
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    bandwidth = safe_div(upper[-1] - lower[-1], middle[-1]) if middle[-1] != 0 else 0
    pct_b = safe_div(data[-1] - lower[-1], upper[-1] - lower[-1]) if (upper[-1] - lower[-1]) != 0 else 0.5
    return upper, middle, lower, bandwidth, pct_b


def analyze_bollinger_bands(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    upper, middle, lower, bw, pct_b = bollinger_bands(close)
    price = close[-1]
    price_prev = close[-2]
    details = {
        "upper": round(upper[-1], 5),
        "middle": round(middle[-1], 5),
        "lower": round(lower[-1], 5),
        "bandwidth": round(bw, 4),
        "pct_b": round(pct_b, 4),
    }
    score = 0.0
    squeeze = bw < np.nanmean([safe_div(upper[i] - lower[i], middle[i]) for i in range(-20, -1) if not np.isnan(middle[i])]) * 0.7
    details["squeeze"] = squeeze

    if pct_b < 0.05:
        score += 0.6
    elif pct_b > 0.95:
        score -= 0.6
    elif pct_b < 0.2:
        score += 0.3
    elif pct_b > 0.8:
        score -= 0.3

    if price > middle[-1]:
        score += 0.15
    else:
        score -= 0.15

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Bollinger Bands", vote, abs(score), 0.78, details)


# ─── GROUP 6: ATR ─────────────────────────────────────────────────────────────

def atr(high, low, close, period=14):
    tr = np.maximum(high[1:] - low[1:],
         np.maximum(np.abs(high[1:] - close[:-1]),
                    np.abs(low[1:] - close[:-1])))
    result = np.full(len(close), np.nan)
    result[period] = np.mean(tr[:period])
    for i in range(period + 1, len(close)):
        result[i] = (result[i - 1] * (period - 1) + tr[i - 1]) / period
    return result


def analyze_atr(df: pd.DataFrame) -> SchoolResult:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    atr_vals = atr(high, low, close)
    current_atr = atr_vals[-1]
    avg_atr = np.nanmean(atr_vals[-50:])
    volatility_ratio = safe_div(current_atr, avg_atr, 1.0)
    details = {
        "atr": round(current_atr, 5),
        "atr_avg_50": round(avg_atr, 5),
        "volatility_ratio": round(volatility_ratio, 3),
        "sl_1_5x": round(current_atr * 1.5, 5),
        "sl_2x": round(current_atr * 2.0, 5),
        "sl_3x": round(current_atr * 3.0, 5),
    }
    return SchoolResult("ATR", Vote.NEUTRAL, 0.5, 0.9, details)


# ─── GROUP 7: ADX ─────────────────────────────────────────────────────────────

def adx(high, low, close, period=14):
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = np.maximum(high[1:] - low[1:],
         np.maximum(np.abs(high[1:] - close[:-1]),
                    np.abs(low[1:] - close[:-1])))
    atr14 = np.full(len(tr), np.nan)
    atr14[period - 1] = np.sum(tr[:period])
    pdm = np.full(len(tr), np.nan)
    mdm = np.full(len(tr), np.nan)
    pdm[period - 1] = np.sum(plus_dm[:period])
    mdm[period - 1] = np.sum(minus_dm[:period])
    for i in range(period, len(tr)):
        atr14[i] = atr14[i - 1] - safe_div(atr14[i - 1], period) + tr[i]
        pdm[i] = pdm[i - 1] - safe_div(pdm[i - 1], period) + plus_dm[i]
        mdm[i] = mdm[i - 1] - safe_div(mdm[i - 1], period) + minus_dm[i]
    pdi = 100 * safe_div(pdm, atr14)
    mdi = 100 * safe_div(mdm, atr14)
    dx = 100 * np.abs(safe_div(pdi - mdi, pdi + mdi))
    adx_val = np.full(len(dx), np.nan)
    adx_val[period * 2 - 2] = np.mean(dx[period - 1:period * 2 - 1])
    for i in range(period * 2 - 1, len(dx)):
        adx_val[i] = (adx_val[i - 1] * (period - 1) + dx[i]) / period
    return adx_val, pdi, mdi


def analyze_adx(df: pd.DataFrame) -> SchoolResult:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    adx_vals, pdi, mdi = adx(high, low, close)
    adx_cur = adx_vals[-1]
    pdi_cur = pdi[-1]
    mdi_cur = mdi[-1]
    details = {
        "adx": round(adx_cur, 2),
        "plus_di": round(pdi_cur, 2),
        "minus_di": round(mdi_cur, 2),
        "trend_strong": bool(adx_cur > 25),
        "sideways": bool(adx_cur < 20),
    }
    score = 0.0
    if adx_cur > 25:
        if pdi_cur > mdi_cur:
            score = min(1.0, (pdi_cur - mdi_cur) / 50)
        else:
            score = -min(1.0, (mdi_cur - pdi_cur) / 50)
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("ADX+DMI", vote, abs(score), 0.82, details)


# ─── GROUP 8: CCI ─────────────────────────────────────────────────────────────

def cci(high, low, close, period=20):
    tp = (high + low + close) / 3
    result = np.full(len(close), np.nan)
    for i in range(period - 1, len(close)):
        tp_slice = tp[i - period + 1:i + 1]
        mean_tp = np.mean(tp_slice)
        mean_dev = np.mean(np.abs(tp_slice - mean_tp))
        result[i] = safe_div(tp[i] - mean_tp, 0.015 * mean_dev)
    return result


def analyze_cci(df: pd.DataFrame) -> SchoolResult:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    cci_vals = cci(high, low, close)
    current = cci_vals[-1]
    details = {"cci": round(current, 2)}
    score = 0.0
    if current > 100:
        score = min(1.0, (current - 100) / 100) * 0.8
    elif current < -100:
        score = -min(1.0, (-current - 100) / 100) * 0.8
    else:
        score = current / 200
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("CCI", vote, abs(score), 0.72, details)


# ─── GROUP 9: ICHIMOKU ───────────────────────────────────────────────────────

def ichimoku(high, low, close, tenkan=9, kijun=26, senkou_b=52, displacement=26):
    def mid(h, l, p):
        result = np.full(len(h), np.nan)
        for i in range(p - 1, len(h)):
            result[i] = (np.max(h[i - p + 1:i + 1]) + np.min(l[i - p + 1:i + 1])) / 2
        return result

    tenkan_sen = mid(high, low, tenkan)
    kijun_sen = mid(high, low, kijun)
    senkou_a = (tenkan_sen + kijun_sen) / 2
    senkou_b_line = mid(high, low, senkou_b)
    chikou = close
    return tenkan_sen, kijun_sen, senkou_a, senkou_b_line, chikou


def analyze_ichimoku(df: pd.DataFrame) -> SchoolResult:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    t, k, sa, sb, chikou = ichimoku(high, low, close)
    price = close[-1]
    details = {
        "tenkan": round(t[-1], 5),
        "kijun": round(k[-1], 5),
        "senkou_a": round(sa[-1], 5),
        "senkou_b": round(sb[-1], 5),
    }
    score = 0.0
    cloud_top = max(sa[-1], sb[-1])
    cloud_bot = min(sa[-1], sb[-1])
    if price > cloud_top:
        score += 0.5
    elif price < cloud_bot:
        score -= 0.5
    if t[-1] > k[-1]:
        score += 0.2
    else:
        score -= 0.2
    if t[-2] < k[-2] and t[-1] > k[-1]:
        score += 0.2
    elif t[-2] > k[-2] and t[-1] < k[-1]:
        score -= 0.2
    if close[-26] > price:
        score += 0.1
    else:
        score -= 0.1
    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.25 else (Vote.SELL if score < -0.25 else Vote.NEUTRAL)
    return SchoolResult("Ichimoku Cloud", vote, abs(score), 0.88, details)


# ─── GROUP 10: PARABOLIC SAR ─────────────────────────────────────────────────

def parabolic_sar(high, low, close, af_start=0.02, af_max=0.2):
    n = len(close)
    sar = np.full(n, np.nan)
    trend = np.ones(n)
    ep = low[0]
    af = af_start
    sar[0] = high[0]
    for i in range(1, n):
        sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
        if trend[i - 1] == 1:
            if low[i] < sar[i]:
                trend[i] = -1
                sar[i] = ep
                ep = low[i]
                af = af_start
            else:
                trend[i] = 1
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + af_start, af_max)
        else:
            if high[i] > sar[i]:
                trend[i] = 1
                sar[i] = ep
                ep = high[i]
                af = af_start
            else:
                trend[i] = -1
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + af_start, af_max)
    return sar, trend


def analyze_parabolic_sar(df: pd.DataFrame) -> SchoolResult:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    sar, trend = parabolic_sar(high, low, close)
    details = {"sar": round(sar[-1], 5), "trend": int(trend[-1])}
    score = float(trend[-1]) * 0.6
    vote = Vote.BUY if trend[-1] > 0 else Vote.SELL
    return SchoolResult("Parabolic SAR", vote, abs(score), 0.70, details)


# ─── GROUP 11: WILLIAMS %R ───────────────────────────────────────────────────

def williams_r(high, low, close, period=14):
    result = np.full(len(close), np.nan)
    for i in range(period - 1, len(close)):
        h = np.max(high[i - period + 1:i + 1])
        l = np.min(low[i - period + 1:i + 1])
        result[i] = safe_div(close[i] - h, h - l) * 100
    return result


def analyze_williams_r(df: pd.DataFrame) -> SchoolResult:
    wr = williams_r(df['high'].values, df['low'].values, df['close'].values)
    cur = wr[-1]
    details = {"williams_r": round(cur, 2)}
    score = 0.0
    if cur < -80:
        score = ((-80 - cur) / 20) * 0.8
    elif cur > -20:
        score = -((cur + 20) / 20) * 0.8
    else:
        score = -(cur + 50) / 60
    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Williams %R", vote, abs(score), 0.72, details)


# ─── GROUP 12: OBV ───────────────────────────────────────────────────────────

def obv(close, volume):
    result = np.zeros(len(close))
    for i in range(1, len(close)):
        if close[i] > close[i - 1]:
            result[i] = result[i - 1] + volume[i]
        elif close[i] < close[i - 1]:
            result[i] = result[i - 1] - volume[i]
        else:
            result[i] = result[i - 1]
    return result


def analyze_obv(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    volume = df['volume'].values
    obv_vals = obv(close, volume)
    obv_ema = ema(obv_vals, 20)
    score = 0.0
    if obv_vals[-1] > obv_ema[-1]:
        score = 0.5
    else:
        score = -0.5
    bull_div, bear_div = detect_divergence(close, obv_vals)
    if bull_div and bull_div[0]:
        score += 0.3
    if bear_div and bear_div[0]:
        score -= 0.3
    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    details = {"obv": round(obv_vals[-1], 2), "obv_ema20": round(obv_ema[-1], 2)}
    return SchoolResult("OBV", vote, abs(score), 0.73, details)


# ─── GROUP 13: MFI ───────────────────────────────────────────────────────────

def mfi(high, low, close, volume, period=14):
    tp = (high + low + close) / 3
    mf = tp * volume
    result = np.full(len(close), np.nan)
    for i in range(period, len(close)):
        pos_mf = sum(mf[j] for j in range(i - period, i) if tp[j] > tp[j - 1])
        neg_mf = sum(mf[j] for j in range(i - period, i) if tp[j] < tp[j - 1])
        mr = safe_div(pos_mf, neg_mf, 100)
        result[i] = 100 - safe_div(100, 1 + mr)
    return result


def analyze_mfi(df: pd.DataFrame) -> SchoolResult:
    mfi_vals = mfi(df['high'].values, df['low'].values, df['close'].values, df['volume'].values)
    cur = mfi_vals[-1]
    details = {"mfi": round(cur, 2)}
    score = 0.0
    if cur < 20:
        score = (20 - cur) / 20 * 0.8
    elif cur > 80:
        score = -((cur - 80) / 20) * 0.8
    else:
        score = (cur - 50) / 60
    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("MFI", vote, abs(score), 0.77, details)


# ─── GROUP 14: VWAP ──────────────────────────────────────────────────────────

def vwap(high, low, close, volume):
    tp = (high + low + close) / 3
    cum_tp_vol = np.cumsum(tp * volume)
    cum_vol = np.cumsum(volume)
    return cum_tp_vol / np.where(cum_vol > 0, cum_vol, 1)


def analyze_vwap(df: pd.DataFrame) -> SchoolResult:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    volume = df['volume'].values
    vwap_vals = vwap(high, low, close, volume)
    price = close[-1]
    vwap_cur = vwap_vals[-1]
    tp = (high + low + close) / 3
    std = np.std(tp[-20:])
    details = {
        "vwap": round(vwap_cur, 5),
        "vwap_plus1": round(vwap_cur + std, 5),
        "vwap_minus1": round(vwap_cur - std, 5),
        "above_vwap": bool(price > vwap_cur),
    }
    score = 0.5 if price > vwap_cur else -0.5
    distance = abs(price - vwap_cur) / vwap_cur
    if distance > 0.02:
        score *= 0.7
    vote = Vote.BUY if score > 0 else Vote.SELL
    return SchoolResult("VWAP", vote, abs(score), 0.80, details)


# ─── GROUP 15: FIBONACCI ─────────────────────────────────────────────────────

FIB_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.618]


def fibonacci_levels(high: float, low: float, direction: str = "up") -> Dict[float, float]:
    diff = high - low
    levels = {}
    for level in FIB_LEVELS:
        if direction == "up":
            levels[level] = high - diff * level
        else:
            levels[level] = low + diff * level
    return levels


def analyze_fibonacci(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    lookback = min(50, len(close))
    recent_high = np.max(high[-lookback:])
    recent_low = np.min(low[-lookback:])
    price = close[-1]
    fib_up = fibonacci_levels(recent_high, recent_low, "up")
    fib_range = recent_high - recent_low
    fib_position = safe_div(price - recent_low, fib_range)

    score = 0.0
    nearest_level = None
    min_dist = float('inf')
    for level, fib_price in fib_up.items():
        dist = abs(price - fib_price)
        if dist < min_dist:
            min_dist = dist
            nearest_level = level
    details = {
        "nearest_fib": nearest_level,
        "fib_position": round(fib_position, 3),
        "recent_high": round(recent_high, 5),
        "recent_low": round(recent_low, 5),
        "level_382": round(fib_up[0.382], 5),
        "level_500": round(fib_up[0.5], 5),
        "level_618": round(fib_up[0.618], 5),
    }
    at_support = any(abs(price - fib_up[l]) < fib_range * 0.01 for l in [0.382, 0.5, 0.618, 0.786])
    if at_support:
        score = 0.6 if fib_position < 0.5 else -0.6
    else:
        score = (0.5 - fib_position) * 0.4
    details["at_key_fib"] = at_support
    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Fibonacci", vote, abs(score), 0.85, details)


# ─── GROUP 16: PIVOT POINTS ──────────────────────────────────────────────────

def pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    pp = (high + low + close) / 3
    r1 = 2 * pp - low
    s1 = 2 * pp - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    r3 = high + 2 * (pp - low)
    s3 = low - 2 * (high - pp)
    return {"PP": pp, "R1": r1, "R2": r2, "R3": r3, "S1": s1, "S2": s2, "S3": s3}


def analyze_pivot_points(df: pd.DataFrame) -> SchoolResult:
    if len(df) < 2:
        return SchoolResult("Pivot Points", Vote.NEUTRAL, 0.5, 0.5, {})
    prev = df.iloc[-2]
    price = df['close'].values[-1]
    pivots = pivot_points(prev['high'], prev['low'], prev['close'])
    score = 0.0
    if price > pivots['R1']:
        score = 0.7
    elif price > pivots['PP']:
        score = 0.4
    elif price < pivots['S1']:
        score = -0.7
    elif price < pivots['PP']:
        score = -0.4
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Pivot Points", vote, abs(score), 0.78, {k: round(v, 5) for k, v in pivots.items()})


# ─── GROUP 17: DONCHIAN CHANNELS ─────────────────────────────────────────────

def donchian_channels(high, low, period=20):
    upper = np.full(len(high), np.nan)
    lower = np.full(len(low), np.nan)
    for i in range(period - 1, len(high)):
        upper[i] = np.max(high[i - period + 1:i + 1])
        lower[i] = np.min(low[i - period + 1:i + 1])
    middle = (upper + lower) / 2
    return upper, middle, lower


def analyze_donchian(df: pd.DataFrame) -> SchoolResult:
    upper, middle, lower = donchian_channels(df['high'].values, df['low'].values)
    price = df['close'].values[-1]
    details = {"upper": round(upper[-1], 5), "middle": round(middle[-1], 5), "lower": round(lower[-1], 5)}
    score = (price - middle[-1]) / (upper[-1] - middle[-1]) if (upper[-1] - middle[-1]) != 0 else 0
    score = max(-1.0, min(1.0, score * 0.6))
    is_breakout_up = price >= upper[-1]
    is_breakout_down = price <= lower[-1]
    if is_breakout_up:
        score = 0.8
    if is_breakout_down:
        score = -0.8
    details["breakout_up"] = is_breakout_up
    details["breakout_down"] = is_breakout_down
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Donchian Channels", vote, abs(score), 0.72, details)


# ─── GROUP 18: KELTNER CHANNELS ──────────────────────────────────────────────

def keltner_channels(high, low, close, period=20, atr_mult=2.0):
    middle = ema(close, period)
    atr_vals = atr(high, low, close, period)
    upper = middle + atr_mult * atr_vals
    lower = middle - atr_mult * atr_vals
    return upper, middle, lower


def analyze_keltner(df: pd.DataFrame) -> SchoolResult:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    upper, middle, lower = keltner_channels(high, low, close)
    price = close[-1]
    details = {"upper": round(upper[-1], 5), "middle": round(middle[-1], 5), "lower": round(lower[-1], 5)}
    score = 0.0
    if price > upper[-1]:
        score = 0.7
    elif price < lower[-1]:
        score = -0.7
    elif price > middle[-1]:
        score = 0.3
    else:
        score = -0.3
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Keltner Channels", vote, abs(score), 0.73, details)


# ─── GROUP 19: AROON ─────────────────────────────────────────────────────────

def aroon(high, low, period=25):
    up = np.full(len(high), np.nan)
    down = np.full(len(low), np.nan)
    for i in range(period, len(high)):
        up[i] = 100 * (period - (i - np.argmax(high[i - period:i + 1]))) / period
        down[i] = 100 * (period - (i - np.argmin(low[i - period:i + 1]))) / period
    return up, down


def analyze_aroon(df: pd.DataFrame) -> SchoolResult:
    up, down = aroon(df['high'].values, df['low'].values)
    up_cur, down_cur = up[-1], down[-1]
    details = {"aroon_up": round(up_cur, 2), "aroon_down": round(down_cur, 2)}
    score = (up_cur - down_cur) / 100
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Aroon", vote, abs(score), 0.70, details)


# ─── GROUP 20: PRICE ACTION ──────────────────────────────────────────────────

def analyze_price_action(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    score = 0.0
    details = {}

    # Higher Highs / Higher Lows
    hh = high[-1] > high[-2] and high[-2] > high[-3]
    hl = low[-1] > low[-2] and low[-2] > low[-3]
    lh = high[-1] < high[-2] and high[-2] < high[-3]
    ll = low[-1] < low[-2] and low[-2] < low[-3]
    details.update({"HH": hh, "HL": hl, "LH": lh, "LL": ll})
    if hh and hl:
        score += 0.5
    elif lh and ll:
        score -= 0.5

    # Pin Bar
    body = abs(close[-1] - df['open'].values[-1])
    candle_range = high[-1] - low[-1]
    upper_wick = high[-1] - max(close[-1], df['open'].values[-1])
    lower_wick = min(close[-1], df['open'].values[-1]) - low[-1]
    pin_bull = lower_wick > 2 * body and lower_wick > upper_wick and candle_range > 0
    pin_bear = upper_wick > 2 * body and upper_wick > lower_wick and candle_range > 0
    details["pin_bar_bull"] = pin_bull
    details["pin_bar_bear"] = pin_bear
    if pin_bull:
        score += 0.35
    if pin_bear:
        score -= 0.35

    # Inside Bar
    inside_bar = high[-1] < high[-2] and low[-1] > low[-2]
    details["inside_bar"] = inside_bar

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Price Action", vote, abs(score), 0.82, details)


# ─── GROUP 21: SMART MONEY (SMC) ─────────────────────────────────────────────

def detect_order_blocks(df: pd.DataFrame, lookback: int = 20) -> List[Dict]:
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    open_ = df['open'].values
    blocks = []
    for i in range(1, min(lookback, len(df) - 1)):
        idx = len(df) - 1 - i
        if close[idx + 1] > high[idx] and (close[idx] < open_[idx]):
            blocks.append({"type": "bullish", "high": high[idx], "low": low[idx],
                           "index": idx, "fresh": True})
        elif close[idx + 1] < low[idx] and (close[idx] > open_[idx]):
            blocks.append({"type": "bearish", "high": high[idx], "low": low[idx],
                           "index": idx, "fresh": True})
    return blocks


def detect_fvg(df: pd.DataFrame) -> List[Dict]:
    high = df['high'].values
    low = df['low'].values
    fvgs = []
    for i in range(2, len(df)):
        bull_fvg = low[i] > high[i - 2]
        bear_fvg = high[i] < low[i - 2]
        if bull_fvg:
            fvgs.append({"type": "bullish", "top": low[i], "bottom": high[i - 2], "index": i})
        elif bear_fvg:
            fvgs.append({"type": "bearish", "top": low[i - 2], "bottom": high[i], "index": i})
    return fvgs[-5:] if fvgs else []


def detect_bos_choch(df: pd.DataFrame) -> Dict:
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    bos_bull = close[-1] > np.max(high[-10:-1])
    bos_bear = close[-1] < np.min(low[-10:-1])
    choch = False
    prev_trend = "up" if high[-5] > high[-10] else "down"
    if prev_trend == "up" and close[-1] < np.min(low[-5:-1]):
        choch = True
    elif prev_trend == "down" and close[-1] > np.max(high[-5:-1]):
        choch = True
    return {"bos_bullish": bos_bull, "bos_bearish": bos_bear, "choch": choch, "prev_trend": prev_trend}


def analyze_smc(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    price = close[-1]
    order_blocks = detect_order_blocks(df)
    fvgs = detect_fvg(df)
    bos = detect_bos_choch(df)
    score = 0.0
    details = {"order_blocks": len(order_blocks), "fvgs": len(fvgs)}
    details.update(bos)

    bull_obs = [b for b in order_blocks if b['type'] == 'bullish' and b['low'] <= price <= b['high']]
    bear_obs = [b for b in order_blocks if b['type'] == 'bearish' and b['low'] <= price <= b['high']]
    if bull_obs:
        score += 0.5
    if bear_obs:
        score -= 0.5

    recent_fvg_bull = [f for f in fvgs if f['type'] == 'bullish' and f['bottom'] <= price <= f['top']]
    recent_fvg_bear = [f for f in fvgs if f['type'] == 'bearish' and f['bottom'] <= price <= f['top']]
    if recent_fvg_bull:
        score += 0.3
    if recent_fvg_bear:
        score -= 0.3

    if bos['bos_bullish']:
        score += 0.25
    if bos['bos_bearish']:
        score -= 0.25
    if bos['choch']:
        score *= -0.5

    swing_range = np.max(high[-50:]) - np.min(low[-50:])
    midpoint = np.min(low[-50:]) + swing_range / 2
    in_discount = price < midpoint
    in_premium = price > midpoint
    details["in_discount"] = in_discount
    details["in_premium"] = in_premium
    if in_discount:
        score += 0.2
    if in_premium:
        score -= 0.2

    score = max(-1.0, min(1.0, score))
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Smart Money Concepts", vote, abs(score), 0.88, details)


# ─── GROUP 22: WYCKOFF ───────────────────────────────────────────────────────

def analyze_wyckoff(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    volume = df['volume'].values
    high = df['high'].values
    low = df['low'].values
    n = min(50, len(df))
    recent_close = close[-n:]
    recent_vol = volume[-n:]
    avg_vol = np.mean(recent_vol)
    price_range = np.max(recent_close) - np.min(recent_close)
    price_position = safe_div(close[-1] - np.min(recent_close), price_range)
    vol_trend = np.mean(recent_vol[-5:]) > np.mean(recent_vol[-20:-5])
    details = {
        "price_position": round(price_position, 3),
        "vol_trend_up": bool(vol_trend),
        "avg_vol": round(avg_vol, 2),
    }
    score = 0.0
    if price_position < 0.3 and vol_trend:
        score = 0.6
        details["phase"] = "Accumulation"
    elif price_position > 0.7 and not vol_trend:
        score = -0.6
        details["phase"] = "Distribution"
    elif price_position > 0.4 and vol_trend:
        score = 0.4
        details["phase"] = "Markup"
    elif price_position < 0.6 and not vol_trend:
        score = -0.4
        details["phase"] = "Markdown"
    else:
        details["phase"] = "Unknown"
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Wyckoff Method", vote, abs(score), 0.80, details)


# ─── GROUP 23: VOLUME SPREAD ANALYSIS ───────────────────────────────────────

def analyze_vsa(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    open_ = df['open'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    spread = high[-1] - low[-1]
    avg_spread = np.mean(high[-20:] - low[-20:])
    avg_vol = np.mean(volume[-20:])
    vol_cur = volume[-1]
    close_pos = safe_div(close[-1] - low[-1], spread) if spread > 0 else 0.5
    score = 0.0
    details = {}
    if vol_cur > avg_vol * 1.5 and spread > avg_spread * 1.2:
        if close_pos > 0.6:
            score = 0.7
            details["signal"] = "Stopping Volume / Effort Up"
        else:
            score = -0.7
            details["signal"] = "Pseudo Upthrust / Distribution"
    elif vol_cur < avg_vol * 0.6 and spread < avg_spread * 0.5:
        details["signal"] = "No Supply / No Demand"
        score = 0.3 if close_pos > 0.5 else -0.3
    else:
        details["signal"] = "Normal"
        score = (close_pos - 0.5) * 0.4
    details.update({"spread": round(spread, 5), "avg_spread": round(avg_spread, 5),
                    "vol": round(vol_cur, 2), "avg_vol": round(avg_vol, 2)})
    vote = Vote.BUY if score > 0.2 else (Vote.SELL if score < -0.2 else Vote.NEUTRAL)
    return SchoolResult("Volume Spread Analysis", vote, abs(score), 0.78, details)


# ─── GROUP 24: HARMONIC PATTERNS ─────────────────────────────────────────────

def analyze_harmonics(df: pd.DataFrame) -> SchoolResult:
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = min(100, len(close))
    recent = close[-n:]
    score = 0.0
    details = {"pattern": "none"}

    if n < 20:
        return SchoolResult("Harmonic Patterns", Vote.NEUTRAL, 0.3, 0.5, details)

    # Simplified Gartley detection
    x = low[-n]
    a = high[np.argmax(high[-n:-n // 2]) + len(high) - n]
    b = low[np.argmin(low[-n // 2:]) + len(low) - n // 2]
    c = close[-1]

    xa = a - x
    ab = a - b
    bc = c - b
    ab_ratio = safe_div(ab, xa)
    bc_ratio = safe_div(bc, ab)

    if 0.55 <= ab_ratio <= 0.65 and 0.35 <= bc_ratio <= 0.45:
        details["pattern"] = "Gartley (bullish)"
        score = 0.65

    vote = Vote.BUY if score > 0.3 else (Vote.SELL if score < -0.3 else Vote.NEUTRAL)
    return SchoolResult("Harmonic Patterns", vote, abs(score), 0.75, details)


# ─── GROUP 25: CANDLESTICK PATTERNS ──────────────────────────────────────────

def analyze_candlestick_patterns(df: pd.DataFrame) -> SchoolResult:
    """Scan 38+ candlestick patterns and aggregate into a vote."""
    try:
        import sys, os
        _dir = os.path.dirname(os.path.abspath(__file__))
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        from candlestick_patterns import aggregate_pattern_vote
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        result = aggregate_pattern_vote(opens, highs, lows, closes)
        vote = Vote(result["vote"]) if result["vote"] in ("BUY", "SELL") else Vote.NEUTRAL
        strength = abs(result.get("score", 0))
        top_patterns = result.get("patterns", [])[:3]
        details = {
            "vote": result["vote"],
            "score": result.get("score", 0),
            "buy_score": result.get("buy_score", 0),
            "sell_score": result.get("sell_score", 0),
            "patterns": [p["pattern"] for p in top_patterns],
        }
        return SchoolResult("Candlestick Patterns", vote, strength, 0.80, details)
    except Exception as e:
        return SchoolResult("Candlestick Patterns", Vote.NEUTRAL, 0.3, 0.5, {"error": str(e)})


# ─── GROUP 26: ELLIOTT WAVE ───────────────────────────────────────────────────

def analyze_elliott_wave_school(df: pd.DataFrame) -> SchoolResult:
    """Elliott Wave analysis."""
    try:
        import sys, os
        _dir = os.path.dirname(os.path.abspath(__file__))
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        from elliott_wave import analyze_elliott_wave
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        result = analyze_elliott_wave(highs, lows, closes)
        direction = result.direction
        vote = Vote.BUY if direction == "BUY" else (Vote.SELL if direction == "SELL" else Vote.NEUTRAL)
        details = {
            "wave": result.wave_count,
            "next_target": result.next_target,
            "invalidation": result.invalidation,
            **result.details,
        }
        return SchoolResult("Elliott Wave", vote, result.confidence, result.confidence * 0.9, details)
    except Exception as e:
        return SchoolResult("Elliott Wave", Vote.NEUTRAL, 0.3, 0.5, {"error": str(e)})


# ─── GROUP 27: GANN ANALYSIS ─────────────────────────────────────────────────

def analyze_gann_school(df: pd.DataFrame) -> SchoolResult:
    """Gann Square of 9 + Fan levels."""
    try:
        import sys, os
        _dir = os.path.dirname(os.path.abspath(__file__))
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        from elliott_wave import analyze_gann
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        result = analyze_gann(highs, lows, closes)
        vote_str = result.get("vote", "NEUTRAL")
        vote = Vote.BUY if vote_str == "BUY" else (Vote.SELL if vote_str == "SELL" else Vote.NEUTRAL)
        return SchoolResult("Gann Analysis", vote, result.get("confidence", 0.5), 0.65, {
            "resistance": result.get("gann_resistance"),
            "support": result.get("gann_support"),
        })
    except Exception as e:
        return SchoolResult("Gann Analysis", Vote.NEUTRAL, 0.3, 0.5, {"error": str(e)})


# ─── GROUP 28: HARMONIC PATTERNS (FULL) ──────────────────────────────────────

def analyze_harmonic_full(df: pd.DataFrame) -> SchoolResult:
    """Full harmonic pattern detection: Gartley, Bat, Butterfly, Crab, Shark, Cypher, AB=CD."""
    try:
        import sys, os
        _dir = os.path.dirname(os.path.abspath(__file__))
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        from elliott_wave import analyze_harmonics_vote
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        result = analyze_harmonics_vote(highs, lows, closes)
        vote_str = result.get("vote", "NEUTRAL")
        vote = Vote.BUY if vote_str == "BUY" else (Vote.SELL if vote_str == "SELL" else Vote.NEUTRAL)
        patterns = [p["name"] for p in result.get("patterns", [])]
        return SchoolResult("Harmonic Patterns", vote, result.get("confidence", 0.3), 0.75, {
            "patterns": patterns,
            "count": len(patterns),
        })
    except Exception as e:
        return SchoolResult("Harmonic Patterns", Vote.NEUTRAL, 0.3, 0.5, {"error": str(e)})


# ─── GROUP 29: DEMARK SEQUENTIAL ─────────────────────────────────────────────

def analyze_demark(df: pd.DataFrame) -> SchoolResult:
    """TD Sequential exhaustion signals."""
    try:
        import sys, os
        _dir = os.path.dirname(os.path.abspath(__file__))
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        from demark import td_sequential, td_combo
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        td = td_sequential(closes, highs, lows)
        combo = td_combo(closes, highs, lows)

        if td.buy_signal or combo.get("signal") == "BUY":
            vote = Vote.BUY
            strength = 0.75
        elif td.sell_signal or combo.get("signal") == "SELL":
            vote = Vote.SELL
            strength = 0.75
        elif (td.td_buy_setup or 0) >= 7:
            vote = Vote.BUY
            strength = 0.4
        elif (td.td_sell_setup or 0) >= 7:
            vote = Vote.SELL
            strength = 0.4
        else:
            vote = Vote.NEUTRAL
            strength = 0.2

        details = {
            "buy_setup": td.td_buy_setup,
            "sell_setup": td.td_sell_setup,
            "buy_countdown": td.td_buy_countdown,
            "sell_countdown": td.td_sell_countdown,
            "buy_exhaustion": td.buy_signal,
            "sell_exhaustion": td.sell_signal,
            "combo_signal": combo.get("signal"),
        }
        return SchoolResult("TD Sequential", vote, strength, 0.78, details)
    except Exception as e:
        return SchoolResult("TD Sequential", Vote.NEUTRAL, 0.3, 0.5, {"error": str(e)})


# ─── MASTER ANALYZER ─────────────────────────────────────────────────────────

_CORE_ANALYZERS = [
    analyze_moving_averages,      # 1
    analyze_rsi,                  # 2
    analyze_macd,                 # 3
    analyze_stochastic,           # 4
    analyze_bollinger_bands,      # 5
    analyze_atr,                  # 6
    analyze_adx,                  # 7
    analyze_cci,                  # 8
    analyze_ichimoku,             # 9
    analyze_parabolic_sar,        # 10
    analyze_williams_r,           # 11
    analyze_obv,                  # 12
    analyze_mfi,                  # 13
    analyze_vwap,                 # 14
    analyze_fibonacci,            # 15
    analyze_pivot_points,         # 16
    analyze_donchian,             # 17
    analyze_keltner,              # 18
    analyze_aroon,                # 19
    analyze_price_action,         # 20
    analyze_smc,                  # 21
    analyze_wyckoff,              # 22
    analyze_vsa,                  # 23
    analyze_harmonics,            # 24
    analyze_candlestick_patterns, # 25
    analyze_elliott_wave_school,  # 26
    analyze_gann_school,          # 27
    analyze_harmonic_full,        # 28
    analyze_demark,               # 29
]


def analyze_all_schools(df: pd.DataFrame) -> List[SchoolResult]:
    """Run all 74 technical schools (29 core + 45 extended) on the given OHLCV DataFrame."""
    if len(df) < 20:
        return []

    from indicators_extended import analyze_all_extended

    results: List[SchoolResult] = []
    for analyzer in _CORE_ANALYZERS:
        try:
            results.append(analyzer(df))
        except Exception:
            pass

    results.extend(analyze_all_extended(df))
    return results
