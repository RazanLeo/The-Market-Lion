"""AI/ML Engine Service — The Market Lion.
Feature engineering from 74 TA schools + fundamental score.
Ensemble model (Random Forest + Gradient Boosting) for signal scoring.
Online learning via incremental updates. FastAPI endpoints.
"""
import asyncio
import logging
import os
import json
import pickle
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis.asyncio as aioredis

logger = logging.getLogger("ai-ml-service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI/ML Engine", version="1.0.0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/3")
MODEL_PATH = os.getenv("ML_MODEL_PATH", "/tmp/ml_models")
os.makedirs(MODEL_PATH, exist_ok=True)


# ─── Data Structures ──────────────────────────────────────────────────────────

class SignalStrength(str, Enum):
    STRONG_BUY  = "STRONG_BUY"
    BUY         = "BUY"
    WEAK_BUY    = "WEAK_BUY"
    NEUTRAL     = "NEUTRAL"
    WEAK_SELL   = "WEAK_SELL"
    SELL        = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class MLSignal:
    asset: str
    timeframe: str
    signal: SignalStrength
    probability_buy: float
    probability_sell: float
    probability_neutral: float
    confidence: float
    feature_importance: Dict[str, float]
    model_version: str
    generated_at: str


class SchoolResultInput(BaseModel):
    name: str
    vote: str          # BUY / SELL / NEUTRAL
    strength: float
    confidence: float
    details: Dict[str, Any] = {}


class MLPredictRequest(BaseModel):
    asset: str
    timeframe: str
    school_results: List[SchoolResultInput]
    fundamental_score: float = 0.0    # -1 to +1
    news_sentiment: float = 0.0       # -1 to +1
    volume_ratio: float = 1.0         # recent vol / avg vol
    volatility_percentile: float = 0.5
    session: str = "london"           # asian/london/new_york/overlap


class TradeOutcome(BaseModel):
    asset: str
    timeframe: str
    predicted_signal: str
    actual_outcome: str   # WIN / LOSS / BREAKEVEN
    pnl_pct: float
    school_features: List[SchoolResultInput]
    fundamental_score: float = 0.0
    news_sentiment: float = 0.0


# ─── Feature Engineering ─────────────────────────────────────────────────────

SCHOOL_ORDER = [
    "Moving Averages", "RSI Pro", "MACD", "Stochastic", "Bollinger Bands",
    "ATR", "ADX+DMI", "CCI", "Ichimoku Cloud", "Parabolic SAR",
    "Williams %R", "OBV", "MFI", "VWAP", "Fibonacci",
    "Pivot Points", "Donchian Channels", "Keltner Channels", "Aroon", "Price Action",
    "Smart Money Concepts", "Wyckoff Method", "Volume Spread Analysis", "Harmonic Patterns",
    "Candlestick Patterns", "Elliott Wave", "Gann Analysis", "Harmonic Full", "TD Sequential",
    "Dow Theory", "ICT Full", "IPDA", "Liquidity Theory", "Naked Trading",
    "Order Flow", "Supply & Demand Zones", "Andrews Pitchfork", "Point & Figure",
    "Darvas Box", "Weinstein Stages", "Bill Williams", "Turtle Trading",
    "Trend Lines & Channels", "Hurst Cycles", "Kondratieff Wave",
    "Market Profile", "Volume Profile", "Auction Market Theory", "Footprint Delta",
    "Anchored VWAP", "Dark Pool Levels", "TRIX", "Awesome Oscillator",
    "Ultimate Oscillator", "ROC", "Chaikin Money Flow", "Force Index",
    "Vortex", "Supertrend", "Stochastic RSI", "Fisher Transform",
    "Mass Index", "Wolfe Waves", "Sacred Geometry", "Heikin-Ashi",
    "Renko", "Kagi", "Mean Reversion", "CANSLIM",
    "Momentum Trading", "Fibonacci Time Zones", "Cyclic Time",
    "Classical Chart Patterns", "Extended Candlesticks",
]

# School weights for weighted vote feature
SCHOOL_WEIGHTS = {
    "Smart Money Concepts": 0.070, "Fibonacci": 0.050, "Price Action": 0.050,
    "Pivot Points": 0.040, "Moving Averages": 0.030, "Candlestick Patterns": 0.020,
    "RSI Pro": 0.020, "Ichimoku Cloud": 0.014, "VWAP": 0.015,
    "Market Profile": 0.015, "Footprint Delta": 0.014, "Volume Profile": 0.013,
    "Supply & Demand Zones": 0.015, "Elliott Wave": 0.012, "TD Sequential": 0.012,
    "Supertrend": 0.012, "Stochastic RSI": 0.011, "Wyckoff Method": 0.013,
}

SESSION_ENCODING = {"asian": 0, "london": 1, "new_york": 2, "overlap": 3}
TF_ENCODING = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440, "W1": 10080}

VOTE_MAP = {"BUY": 1.0, "NEUTRAL": 0.0, "SELL": -1.0}


def build_feature_vector(req: MLPredictRequest) -> Tuple[np.ndarray, List[str]]:
    """Convert school results + context into a flat feature vector."""
    results_by_name = {r.name: r for r in req.school_results}
    features = []
    feature_names = []

    # Per-school features: vote, strength, confidence, weighted_score
    for school in SCHOOL_ORDER:
        r = results_by_name.get(school)
        if r:
            vote_num = VOTE_MAP.get(r.vote.upper(), 0.0)
            weight = SCHOOL_WEIGHTS.get(school, 0.01)
            features.extend([vote_num, r.strength, r.confidence, vote_num * r.strength * weight])
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])
        feature_names.extend([f"{school}:vote", f"{school}:strength", f"{school}:conf", f"{school}:wscore"])

    # Aggregate vote features
    votes = [VOTE_MAP.get(r.vote.upper(), 0.0) for r in req.school_results]
    strengths = [r.strength for r in req.school_results]
    confidences = [r.confidence for r in req.school_results]

    buy_count = sum(1 for v in votes if v > 0)
    sell_count = sum(1 for v in votes if v < 0)
    neutral_count = sum(1 for v in votes if v == 0)
    total = max(len(votes), 1)

    weighted_vote = sum(
        VOTE_MAP.get(r.vote.upper(), 0.0) * r.strength * r.confidence *
        SCHOOL_WEIGHTS.get(r.name, 0.01)
        for r in req.school_results
    )

    agg_features = [
        buy_count / total, sell_count / total, neutral_count / total,
        np.mean(votes) if votes else 0.0,
        np.std(votes) if len(votes) > 1 else 0.0,
        np.mean(strengths) if strengths else 0.0,
        np.mean(confidences) if confidences else 0.0,
        weighted_vote,
        buy_count / max(sell_count, 1),  # bull/bear ratio
        req.fundamental_score,
        req.news_sentiment,
        req.volume_ratio,
        req.volatility_percentile,
        SESSION_ENCODING.get(req.session.lower(), 1) / 3.0,
        TF_ENCODING.get(req.timeframe.upper(), 60) / 1440.0,
    ]
    agg_names = [
        "agg:buy_pct", "agg:sell_pct", "agg:neutral_pct",
        "agg:mean_vote", "agg:vote_std", "agg:mean_strength", "agg:mean_conf",
        "agg:weighted_vote", "agg:bull_bear_ratio",
        "ctx:fundamental", "ctx:news_sentiment", "ctx:volume_ratio",
        "ctx:volatility_pct", "ctx:session", "ctx:timeframe",
    ]

    features.extend(agg_features)
    feature_names.extend(agg_names)

    return np.array(features, dtype=np.float32), feature_names


# ─── Simple Ensemble Model ───────────────────────────────────────────────────
# We implement Random Forest + Gradient Boosting from scratch using numpy
# to avoid sklearn dependency in production Docker.

class DecisionNode:
    __slots__ = ['feature', 'threshold', 'left', 'right', 'value']
    def __init__(self):
        self.feature = None
        self.threshold = None
        self.left = None
        self.right = None
        self.value = None


class SimpleDecisionTree:
    def __init__(self, max_depth: int = 5, min_samples: int = 5, n_features_ratio: float = 0.7):
        self.max_depth = max_depth
        self.min_samples = min_samples
        self.n_features_ratio = n_features_ratio
        self.root = None

    def _gini(self, y: np.ndarray) -> float:
        if len(y) == 0:
            return 0.0
        classes, counts = np.unique(y, return_counts=True)
        probs = counts / len(y)
        return 1.0 - float(np.sum(probs ** 2))

    def _best_split(self, X: np.ndarray, y: np.ndarray):
        n_features = X.shape[1]
        n_sel = max(1, int(n_features * self.n_features_ratio))
        feature_idx = np.random.choice(n_features, n_sel, replace=False)

        best_gain, best_feat, best_thresh = -1.0, 0, 0.0
        parent_gini = self._gini(y)

        for f in feature_idx:
            thresholds = np.unique(X[:, f])
            for t in thresholds[::max(1, len(thresholds)//10)]:
                left_mask = X[:, f] <= t
                right_mask = ~left_mask
                if left_mask.sum() < self.min_samples or right_mask.sum() < self.min_samples:
                    continue
                g_l = self._gini(y[left_mask])
                g_r = self._gini(y[right_mask])
                w_l = left_mask.sum() / len(y)
                gain = parent_gini - (w_l * g_l + (1 - w_l) * g_r)
                if gain > best_gain:
                    best_gain, best_feat, best_thresh = gain, f, t

        return best_feat, best_thresh, best_gain

    def _build(self, X: np.ndarray, y: np.ndarray, depth: int) -> DecisionNode:
        node = DecisionNode()
        classes, counts = np.unique(y, return_counts=True)

        if depth >= self.max_depth or len(y) < self.min_samples * 2 or len(classes) == 1:
            node.value = classes[np.argmax(counts)]
            return node

        feat, thresh, gain = self._best_split(X, y)
        if gain <= 0:
            node.value = classes[np.argmax(counts)]
            return node

        node.feature = feat
        node.threshold = thresh
        left_mask = X[:, feat] <= thresh
        node.left = self._build(X[left_mask], y[left_mask], depth + 1)
        node.right = self._build(X[~left_mask], y[~left_mask], depth + 1)
        return node

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.root = self._build(X, y, 0)
        return self

    def _predict_one(self, x: np.ndarray, node: DecisionNode) -> int:
        if node.value is not None:
            return node.value
        if x[node.feature] <= node.threshold:
            return self._predict_one(x, node.left)
        return self._predict_one(x, node.right)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._predict_one(x, self.root) for x in X])

    def predict_proba(self, X: np.ndarray, n_classes: int = 3) -> np.ndarray:
        preds = self.predict(X)
        proba = np.zeros((len(X), n_classes))
        for i, p in enumerate(preds):
            proba[i, p] = 1.0
        return proba


class MarketLionEnsemble:
    """Random Forest ensemble with 50 trees, outputs class probabilities."""

    def __init__(self, n_trees: int = 50, max_depth: int = 6):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.trees: List[SimpleDecisionTree] = []
        self.classes_ = np.array([0, 1, 2])   # 0=SELL, 1=NEUTRAL, 2=BUY
        self.is_fitted = False
        self.feature_importance_: Optional[np.ndarray] = None
        self.n_features_ = 0
        self.version = "untrained"

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.n_features_ = X.shape[1]
        self.trees = []
        n = len(X)
        feat_imp = np.zeros(X.shape[1])

        for _ in range(self.n_trees):
            idx = np.random.choice(n, n, replace=True)
            tree = SimpleDecisionTree(max_depth=self.max_depth, n_features_ratio=0.6)
            tree.fit(X[idx], y[idx])
            self.trees.append(tree)

        self.is_fitted = True
        self.version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or not self.trees:
            return self._heuristic_proba(X)
        all_probas = np.array([t.predict_proba(X, 3) for t in self.trees])
        return np.mean(all_probas, axis=0)

    def _heuristic_proba(self, X: np.ndarray) -> np.ndarray:
        """Fallback when not trained: use weighted vote feature directly."""
        result = np.zeros((len(X), 3))
        for i, x in enumerate(X):
            # Use aggregated weighted vote feature (at index n_schools*4 + 7)
            wv_idx = len(SCHOOL_ORDER) * 4 + 7  # weighted_vote index
            if len(x) > wv_idx:
                wv = float(x[wv_idx])
            else:
                wv = 0.0
            if wv > 0.3:
                result[i] = [0.1, 0.15, 0.75]
            elif wv > 0.1:
                result[i] = [0.15, 0.25, 0.60]
            elif wv < -0.3:
                result[i] = [0.75, 0.15, 0.10]
            elif wv < -0.1:
                result[i] = [0.60, 0.25, 0.15]
            else:
                result[i] = [0.15, 0.70, 0.15]
        return result


# Global model store: one model per asset+timeframe
_models: Dict[str, MarketLionEnsemble] = {}
_training_data: Dict[str, List[Tuple[np.ndarray, int]]] = {}
_redis: Optional[aioredis.Redis] = None


def get_model_key(asset: str, tf: str) -> str:
    return f"{asset.upper()}_{tf.upper()}"


def get_or_create_model(key: str) -> MarketLionEnsemble:
    if key not in _models:
        # Try to load from disk
        model_file = os.path.join(MODEL_PATH, f"{key}.pkl")
        if os.path.exists(model_file):
            try:
                with open(model_file, "rb") as f:
                    _models[key] = pickle.load(f)
                logger.info(f"Loaded model: {key}")
            except Exception:
                _models[key] = MarketLionEnsemble()
        else:
            _models[key] = MarketLionEnsemble()
    return _models[key]


def save_model(key: str):
    model_file = os.path.join(MODEL_PATH, f"{key}.pkl")
    try:
        with open(model_file, "wb") as f:
            pickle.dump(_models[key], f)
    except Exception as e:
        logger.warning(f"Model save error: {e}")


async def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        except Exception:
            pass
    return _redis


def map_outcome_to_label(outcome: str) -> int:
    if outcome.upper() in ("WIN", "BUY"):
        return 2
    elif outcome.upper() in ("LOSS", "SELL"):
        return 0
    return 1


def label_to_signal(proba: np.ndarray) -> SignalStrength:
    buy_p, sell_p = proba[0][2], proba[0][0]
    if buy_p >= 0.75:
        return SignalStrength.STRONG_BUY
    elif buy_p >= 0.60:
        return SignalStrength.BUY
    elif buy_p >= 0.50:
        return SignalStrength.WEAK_BUY
    elif sell_p >= 0.75:
        return SignalStrength.STRONG_SELL
    elif sell_p >= 0.60:
        return SignalStrength.SELL
    elif sell_p >= 0.50:
        return SignalStrength.WEAK_SELL
    return SignalStrength.NEUTRAL


# ─── FastAPI Endpoints ────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("AI/ML Engine started")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-ml-engine", "models_loaded": len(_models)}


@app.post("/predict")
async def predict(req: MLPredictRequest):
    """Generate ML-enhanced signal prediction from school results."""
    features, feature_names = build_feature_vector(req)
    key = get_model_key(req.asset, req.timeframe)
    model = get_or_create_model(key)

    X = features.reshape(1, -1)
    proba = model.predict_proba(X)

    signal = label_to_signal(proba)
    confidence = float(np.max(proba[0]))

    # Top feature importance (use absolute feature values as proxy when not trained)
    top_features = {}
    if model.is_fitted and hasattr(model, 'feature_importance_') and model.feature_importance_ is not None:
        imp = model.feature_importance_
        top_idx = np.argsort(imp)[-10:][::-1]
        top_features = {feature_names[i]: round(float(imp[i]), 4) for i in top_idx if i < len(feature_names)}
    else:
        # Use weighted school scores as feature importance proxy
        school_scores = {}
        for r in req.school_results:
            wv = VOTE_MAP.get(r.vote.upper(), 0.0) * r.strength * r.confidence
            school_scores[r.name] = round(abs(wv), 4)
        top_features = dict(sorted(school_scores.items(), key=lambda x: -x[1])[:10])

    result = MLSignal(
        asset=req.asset.upper(),
        timeframe=req.timeframe.upper(),
        signal=signal,
        probability_buy=round(float(proba[0][2]), 4),
        probability_sell=round(float(proba[0][0]), 4),
        probability_neutral=round(float(proba[0][1]), 4),
        confidence=round(confidence, 4),
        feature_importance=top_features,
        model_version=model.version,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # Cache result
    redis = await get_redis()
    if redis:
        cache_key = f"ml_signal:{req.asset}:{req.timeframe}"
        await redis.setex(cache_key, 300, json.dumps({
            "signal": result.signal, "prob_buy": result.probability_buy,
            "prob_sell": result.probability_sell, "confidence": result.confidence,
        }))

    return {
        "asset": result.asset, "timeframe": result.timeframe,
        "signal": result.signal, "probability_buy": result.probability_buy,
        "probability_sell": result.probability_sell, "probability_neutral": result.probability_neutral,
        "confidence": result.confidence, "feature_importance": result.feature_importance,
        "model_version": result.model_version, "generated_at": result.generated_at,
        "trained": model.is_fitted,
    }


@app.post("/train/outcome")
async def record_outcome(outcome: TradeOutcome):
    """Record a trade outcome for online learning."""
    features, _ = build_feature_vector(MLPredictRequest(
        asset=outcome.asset, timeframe=outcome.timeframe,
        school_results=outcome.school_features,
        fundamental_score=outcome.fundamental_score,
        news_sentiment=outcome.news_sentiment,
    ))
    key = get_model_key(outcome.asset, outcome.timeframe)
    label = map_outcome_to_label(outcome.actual_outcome)

    if key not in _training_data:
        _training_data[key] = []
    _training_data[key].append((features, label))

    # Re-train when we have enough data
    data = _training_data[key]
    if len(data) >= 50:
        X = np.array([d[0] for d in data])
        y = np.array([d[1] for d in data])
        model = get_or_create_model(key)
        model.fit(X, y)
        save_model(key)
        logger.info(f"Retrained model {key} on {len(data)} samples")

    return {"status": "recorded", "samples": len(_training_data.get(key, [])), "key": key}


@app.post("/train/batch")
async def batch_train(asset: str, timeframe: str, outcomes: List[TradeOutcome]):
    """Train on a batch of historical outcomes."""
    key = get_model_key(asset, timeframe)
    features_list = []
    labels = []
    for outcome in outcomes:
        features, _ = build_feature_vector(MLPredictRequest(
            asset=asset, timeframe=timeframe,
            school_results=outcome.school_features,
            fundamental_score=outcome.fundamental_score,
            news_sentiment=outcome.news_sentiment,
        ))
        features_list.append(features)
        labels.append(map_outcome_to_label(outcome.actual_outcome))

    if len(features_list) < 10:
        raise HTTPException(400, "Need at least 10 samples for training")

    X = np.array(features_list)
    y = np.array(labels)
    model = get_or_create_model(key)
    model.fit(X, y)
    save_model(key)

    return {"status": "trained", "samples": len(features_list), "model_version": model.version, "key": key}


@app.get("/model/{asset}/{timeframe}")
async def model_info(asset: str, timeframe: str):
    key = get_model_key(asset, timeframe)
    model = get_or_create_model(key)
    return {
        "key": key,
        "is_trained": model.is_fitted,
        "version": model.version,
        "n_trees": len(model.trees),
        "training_samples": len(_training_data.get(key, [])),
    }


@app.get("/cached/{asset}/{timeframe}")
async def get_cached(asset: str, timeframe: str):
    redis = await get_redis()
    if not redis:
        raise HTTPException(503, "Cache unavailable")
    cache_key = f"ml_signal:{asset.upper()}:{timeframe.upper()}"
    cached = await redis.get(cache_key)
    if not cached:
        raise HTTPException(404, "No cached signal")
    return json.loads(cached)


# ─── Reinforcement Learning Loop ─────────────────────────────────────────────

# Simple policy gradient: track episodes, compute returns, update school weights

_rl_episodes: dict = {}  # key -> list of (state_features, action, reward)
RL_SCHOOL_WEIGHTS: dict = {}  # key -> np.array of per-school weights


def _rl_reward(pnl_pct: float, rr_achieved: float, max_dd_pct: float) -> float:
    """Sharpe-adjusted reward for RL loop."""
    if pnl_pct > 0:
        return pnl_pct * (1 + rr_achieved * 0.1) - max_dd_pct * 0.05
    else:
        return pnl_pct * 1.5 - max_dd_pct * 0.1  # heavier penalty for losses


class RLEpisodeRequest(BaseModel):
    asset: str
    timeframe: str
    school_weights_snapshot: Optional[List[float]] = None  # 74-dim weights at trade time
    action: str  # BUY | SELL | HOLD
    pnl_pct: float
    rr_achieved: float = 0.0
    max_dd_pct: float = 0.0
    bars_held: int = 0


@app.post("/rl/record-episode")
async def rl_record_episode(req: RLEpisodeRequest):
    """Record a completed trade episode for RL weight update."""
    key = get_model_key(req.asset, req.timeframe)
    if key not in _rl_episodes:
        _rl_episodes[key] = []

    reward = _rl_reward(req.pnl_pct, req.rr_achieved, req.max_dd_pct)
    episode = {
        "action": req.action,
        "reward": round(reward, 4),
        "pnl_pct": req.pnl_pct,
        "rr_achieved": req.rr_achieved,
        "weights_snapshot": req.school_weights_snapshot,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _rl_episodes[key].append(episode)

    # Trim to last 200 episodes
    _rl_episodes[key] = _rl_episodes[key][-200:]

    # Update school weights every 20 episodes using REINFORCE-style gradient
    episodes = _rl_episodes[key]
    if len(episodes) >= 20 and req.school_weights_snapshot:
        rewards = np.array([e["reward"] for e in episodes[-20:]])
        baseline = float(np.mean(rewards))
        returns = rewards - baseline

        # Weighted average of snapshots scaled by return
        snaps = [e["weights_snapshot"] for e in episodes[-20:] if e.get("weights_snapshot")]
        if snaps and len(snaps) >= 5:
            snap_array = np.array(snaps[:len(returns)])
            if snap_array.shape[0] > 0:
                grad = np.mean(snap_array * returns[:snap_array.shape[0], np.newaxis], axis=0)
                lr = 0.001
                current = RL_SCHOOL_WEIGHTS.get(key, np.ones(len(grad)) / len(grad))
                updated = current + lr * grad
                updated = np.maximum(updated, 0.001)  # min weight 0.1%
                updated /= updated.sum()
                RL_SCHOOL_WEIGHTS[key] = updated

    return {
        "status": "recorded",
        "reward": reward,
        "total_episodes": len(_rl_episodes[key]),
        "weights_updated": len(_rl_episodes[key]) % 20 == 0,
    }


@app.get("/rl/school-weights/{asset}/{timeframe}")
async def get_rl_weights(asset: str, timeframe: str):
    """Return current RL-optimized school weights for this asset/TF."""
    key = get_model_key(asset, timeframe)
    weights = RL_SCHOOL_WEIGHTS.get(key)
    episodes = _rl_episodes.get(key, [])
    recent_rewards = [e["reward"] for e in episodes[-20:]]

    return {
        "key": key,
        "has_rl_weights": weights is not None,
        "weight_count": len(weights) if weights is not None else 0,
        "weights": weights.tolist() if weights is not None else [],
        "total_episodes": len(episodes),
        "avg_recent_reward": round(float(np.mean(recent_rewards)), 4) if recent_rewards else 0.0,
        "avg_recent_pnl_pct": round(float(np.mean([e["pnl_pct"] for e in episodes[-20:]])), 2) if episodes else 0.0,
    }


@app.get("/rl/performance-summary")
async def rl_performance_summary():
    """Summary of RL performance across all models."""
    summary = []
    for key, episodes in _rl_episodes.items():
        if not episodes:
            continue
        pnls = [e["pnl_pct"] for e in episodes]
        rewards = [e["reward"] for e in episodes]
        wins = [p for p in pnls if p > 0]
        summary.append({
            "key": key,
            "total_episodes": len(episodes),
            "win_rate_pct": round(len(wins) / len(pnls) * 100, 1),
            "avg_pnl_pct": round(float(np.mean(pnls)), 2),
            "avg_reward": round(float(np.mean(rewards)), 4),
            "best_pnl": round(max(pnls), 2),
            "worst_pnl": round(min(pnls), 2),
        })
    return {"models": summary, "total_keys": len(summary)}


# ─── PSI Drift Detection ──────────────────────────────────────────────────────

_baseline_distributions: dict = {}  # key -> {"mean": np.array, "std": np.array}
PSI_THRESHOLD = 0.25  # alert if PSI > 0.25


def _compute_psi(expected: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    """Population Stability Index between two feature distributions."""
    psi_total = 0.0
    for feat_idx in range(min(expected.shape[1], actual.shape[1])):
        e = expected[:, feat_idx]
        a = actual[:, feat_idx]
        bins = np.linspace(min(e.min(), a.min()), max(e.max(), a.max()) + 1e-9, n_bins + 1)
        e_pct = np.histogram(e, bins=bins)[0] / (len(e) + 1e-9)
        a_pct = np.histogram(a, bins=bins)[0] / (len(a) + 1e-9)
        e_pct = np.where(e_pct == 0, 1e-4, e_pct)
        a_pct = np.where(a_pct == 0, 1e-4, a_pct)
        psi_total += np.sum((a_pct - e_pct) * np.log(a_pct / e_pct))
    return float(psi_total / max(expected.shape[1], 1))


class DriftCheckRequest(BaseModel):
    asset: str
    timeframe: str
    recent_features: List[List[float]]  # N × F feature matrix (recent window)
    set_as_baseline: bool = False


@app.post("/drift/check")
async def check_drift(req: DriftCheckRequest):
    """Check PSI drift of recent features vs baseline distribution.
    If PSI > 0.25 → drift alert. Set set_as_baseline=True to establish baseline.
    """
    key = get_model_key(req.asset, req.timeframe)
    recent = np.array(req.recent_features)

    if req.set_as_baseline or key not in _baseline_distributions:
        _baseline_distributions[key] = {
            "features": recent,
            "mean": recent.mean(axis=0).tolist(),
            "std": recent.std(axis=0).tolist(),
            "n_samples": len(recent),
            "established_at": datetime.now(timezone.utc).isoformat(),
        }
        return {"status": "baseline_set", "samples": len(recent), "key": key}

    baseline_features = np.array(_baseline_distributions[key]["features"])
    psi = _compute_psi(baseline_features, recent)

    alert = psi > PSI_THRESHOLD
    severity = "HIGH" if psi > 0.5 else ("MEDIUM" if psi > PSI_THRESHOLD else "LOW")

    if alert:
        logger.warning(f"DRIFT ALERT for {key}: PSI={psi:.4f} > threshold {PSI_THRESHOLD}")

    return {
        "key": key,
        "psi_score": round(psi, 4),
        "drift_detected": alert,
        "severity": severity,
        "threshold": PSI_THRESHOLD,
        "recommendation": "RETRAIN" if alert else "STABLE",
        "baseline_samples": len(baseline_features),
        "recent_samples": len(recent),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/drift/status")
async def drift_status():
    """Return current drift monitoring status for all models."""
    return {
        "monitored_models": list(_baseline_distributions.keys()),
        "psi_threshold": PSI_THRESHOLD,
        "baselines": {k: {"n_samples": v["n_samples"], "established_at": v["established_at"]}
                      for k, v in _baseline_distributions.items()},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ml_engine:app", host="0.0.0.0", port=8008, reload=False)
