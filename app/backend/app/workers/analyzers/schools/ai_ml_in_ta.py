"""AI/ML in TA — logistic regression on a feature vector to predict direction probability.

Features for each bar (shifted to avoid leakage): ROC(5), RSI(14), MACD signal, BB %B, log(volume) z-score.
Label = sign of forward 10-bar return.
Train on last 200 bars (excluding most recent 10), predict on latest bar.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "ai_ml_in_ta"
WEIGHT_DEFAULT = 0.95


def _features(df: pd.DataFrame) -> pd.DataFrame:
    c = df["c"]; h = df["h"]; l = df["l"]
    roc5 = (c - c.shift(5)) / c.shift(5)
    delta = c.diff()
    up = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    dn = -delta.where(delta < 0, 0).ewm(alpha=1/14, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    sig = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - sig
    sma20 = c.rolling(20).mean()
    sd20 = c.rolling(20).std().replace(0, 1e-9)
    pctb = (c - (sma20 - 2 * sd20)) / (4 * sd20)
    if "v" in df.columns:
        v = df["v"].fillna(1.0)
        log_v = np.log1p(v)
        v_z = (log_v - log_v.rolling(50).mean()) / log_v.rolling(50).std().replace(0, 1e-9)
    else:
        v_z = pd.Series(0.0, index=df.index)
    return pd.DataFrame({"roc5": roc5, "rsi": rsi, "macd_hist": macd_hist,
                         "pctb": pctb, "v_z": v_z}, index=df.index)


def _logistic_fit(X: np.ndarray, y: np.ndarray, lr: float = 0.05, iters: int = 200) -> np.ndarray:
    n, k = X.shape
    Xb = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(k + 1)
    for _ in range(iters):
        z = Xb @ w
        p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
        grad = Xb.T @ (p - y) / n
        w -= lr * grad
    return w


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 230:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    feats = _features(df).iloc[-220:].copy()
    fwd = df["c"].shift(-10) / df["c"] - 1
    label = (fwd > 0).astype(float)
    train = feats.iloc[:-15]
    train_y = label.iloc[-220:].iloc[:-15]
    valid = train.dropna()
    valid_y = train_y.loc[valid.index]
    if len(valid) < 80:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    # Standardize
    mu = valid.mean().values; sd = valid.std().replace(0, 1e-9).values
    Xtr = ((valid.values - mu) / sd).astype(float)
    ytr = valid_y.values.astype(float)
    w = _logistic_fit(Xtr, ytr)
    last = feats.iloc[-1]
    if last.isna().any():
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    x = ((last.values - mu) / sd).astype(float)
    z = float(w[0] + np.dot(w[1:], x))
    p_up = float(1 / (1 + np.exp(-np.clip(z, -30, 30))))
    payload = {"P_up": round(p_up, 3),
               "features": {k: round(float(last[k]), 4) for k in feats.columns},
               "training_samples": int(len(valid))}
    if p_up >= 0.65: return AnalyzerResult(CODE, "buy", min(90.0, p_up * 100), WEIGHT_DEFAULT, payload)
    if p_up <= 0.35: return AnalyzerResult(CODE, "sell", min(90.0, (1 - p_up) * 100), WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class AiMlInTaAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
