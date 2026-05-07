"""COT proxy — derive commercials/non-commercials net positioning from price-volume action.

Without direct CFTC feed, we approximate:
  • Large-trader = aggressive volume bars (volume > 2σ). Their direction = bar sign.
  • Commercial = absorption candles: wide spread + close in middle third + above-average volume.
Track net (signed) position over last 26 bars (~weekly proxy).
Commercial extreme (z>1.5 or z<-1.5) = contrarian signal.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ...engines.voting_engine import AnalyzerResult

CODE = "commitment_of_traders"
WEIGHT_DEFAULT = 0.7


def analyze(df: pd.DataFrame) -> AnalyzerResult:
    if len(df) < 60 or "v" not in df.columns:
        return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, {})
    v = df["v"].fillna(0)
    avg_v = float(v.rolling(50).mean().iloc[-1] or 1)
    vol_z = (v - v.rolling(50).mean()) / v.rolling(50).std().replace(0, 1e-9)
    # Large traders
    large_mask = vol_z > 2
    large_dir = np.sign(df["c"] - df["o"]).where(large_mask, 0)
    large_net_26 = float(large_dir.iloc[-26:].sum())
    # Commercials (absorption)
    rng = (df["h"] - df["l"]).replace(0, 1e-9)
    body = (df["c"] - df["o"]).abs()
    close_pos = (df["c"] - df["l"]) / rng
    absorbing = (rng > rng.rolling(20).mean() * 1.3) & (close_pos > 0.33) & (close_pos < 0.66) & (v > avg_v * 1.2)
    # Commercials act contrarian to large trader move; their direction inferred from prior trend
    prior_trend = np.sign(df["c"] - df["c"].shift(5))
    commercial_dir = (-prior_trend).where(absorbing, 0)
    commercial_net_26 = float(commercial_dir.iloc[-26:].sum())
    # z-score of commercial net over last 200 bars
    commercial_series = (-prior_trend).where(absorbing, 0).rolling(26).sum()
    cm_mean = float(commercial_series.iloc[-200:].mean()) if len(commercial_series) >= 200 else 0
    cm_std = float(commercial_series.iloc[-200:].std() or 1)
    commercial_z = (commercial_net_26 - cm_mean) / cm_std
    payload = {"large_trader_net_26": large_net_26, "commercial_net_26": commercial_net_26,
               "commercial_z": round(commercial_z, 2)}
    if commercial_z > 1.5: return AnalyzerResult(CODE, "buy", 65, WEIGHT_DEFAULT, payload)
    if commercial_z < -1.5: return AnalyzerResult(CODE, "sell", 65, WEIGHT_DEFAULT, payload)
    if large_net_26 > 5: return AnalyzerResult(CODE, "buy", 40, WEIGHT_DEFAULT, payload)
    if large_net_26 < -5: return AnalyzerResult(CODE, "sell", 40, WEIGHT_DEFAULT, payload)
    return AnalyzerResult(CODE, "neutral", 0, WEIGHT_DEFAULT, payload)


class CommitmentOfTradersAnalyzer:
    code = CODE; weight_default = WEIGHT_DEFAULT
    @staticmethod
    def analyze(df): return analyze(df)
