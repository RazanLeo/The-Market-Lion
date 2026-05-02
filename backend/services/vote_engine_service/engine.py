"""Multi-School Voting Engine - The Market Lion."""
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..technical_analysis_service.indicators import SchoolResult, Vote


SCHOOL_WEIGHTS = {
    # Group A: Owner's Core Tools (30%)
    "Smart Money Concepts":     0.070,
    "Fibonacci":                0.050,
    "Price Action":             0.050,
    "Pivot Points":             0.040,
    "Moving Averages":          0.030,
    "Classical Patterns":       0.020,
    "RSI Pro":                  0.020,
    "Candlestick Patterns":     0.020,

    # Group B: Fundamental (20%) - injected externally
    "Fundamental News":         0.120,
    "COT Dark Pool Options":    0.050,
    "Social Intelligence":      0.030,

    # Group C: Remaining schools (50%)
    "ICT Killzones":            0.025,
    "IPDA":                     0.020,
    "Liquidity Theory":         0.020,
    "Judas Swing":              0.018,
    "Silver Bullet":            0.017,
    "Volume Spread Analysis":   0.015,
    "Market Profile":           0.015,
    "VWAP":                     0.015,
    "Footprint Delta":          0.014,
    "Dark Pool":                0.013,
    "Volume Profile":           0.013,
    "Wyckoff Method":           0.013,
    "MACD":                     0.012,
    "Stochastic":               0.012,
    "Bollinger Bands":          0.012,
    "ATR":                      0.010,
    "ADX+DMI":                  0.012,
    "CCI":                      0.010,
    "Ichimoku Cloud":           0.014,
    "Parabolic SAR":            0.010,
    "Williams %R":              0.010,
    "Aroon":                    0.009,
    "OBV":                      0.010,
    "MFI":                      0.010,
    "Donchian Channels":        0.009,
    "Keltner Channels":         0.009,
    "Elliott Wave":             0.012,
    "Wyckoff Cycles":           0.012,
    "Hurst Cycles":             0.010,
    "DeMark Sequential":        0.012,
    "Harmonic Patterns":        0.010,
    "Gann Analysis":            0.009,
    "Supply Demand Zones":      0.015,
    "Order Blocks":             0.015,
    "Intermarket Analysis":     0.008,
    "Seasonality":              0.006,
    "Mean Reversion":           0.007,
    "Market Breadth":           0.006,
}


@dataclass
class VoteResult:
    side: str
    confluence_score: float
    buy_votes: int
    sell_votes: int
    neutral_votes: int
    total_votes: int
    weighted_score: float
    school_breakdown: List[Dict]
    mtf_aligned: bool
    fundamental_aligned: bool
    killzone_active: bool
    should_trade: bool
    rejection_reasons: List[str]
    top_factors: List[Dict]


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def vote_to_score(vote: Vote) -> float:
    return 1.0 if vote == Vote.BUY else (-1.0 if vote == Vote.SELL else 0.0)


def run_vote_engine(
    school_results: List[SchoolResult],
    fundamental_score: float,
    fundamental_direction: str,
    mtf_aligned: bool,
    killzone_active: bool,
    news_shield: bool,
    drawdown_pct: float,
    daily_loss_pct: float,
    consecutive_losses: int,
    market_regime: str = "NEUTRAL",
) -> VoteResult:
    weights = normalize_weights(SCHOOL_WEIGHTS)
    weighted_sum = 0.0
    total_weight = 0.0
    buy_votes = sell_votes = neutral_votes = 0
    breakdown = []

    for result in school_results:
        w = weights.get(result.name, 0.005)
        s = vote_to_score(result.vote) * result.strength
        weighted_sum += s * w * result.confidence
        total_weight += w * result.confidence
        if result.vote == Vote.BUY:
            buy_votes += 1
        elif result.vote == Vote.SELL:
            sell_votes += 1
        else:
            neutral_votes += 1
        breakdown.append({
            "school": result.name,
            "vote": result.vote.value,
            "strength": round(result.strength, 3),
            "confidence": round(result.confidence, 3),
            "weight": round(w, 4),
        })

    # Inject fundamental
    fund_score_norm = (fundamental_score / 100) * (1.0 if fundamental_direction == "BULL" else (-1.0 if fundamental_direction == "BEAR" else 0.0))
    fund_weight = weights.get("Fundamental News", 0.12)
    cot_weight = weights.get("COT Dark Pool Options", 0.05)
    weighted_sum += fund_score_norm * fund_weight
    total_weight += fund_weight

    if total_weight > 0:
        normalized = weighted_sum / total_weight
    else:
        normalized = 0.0

    confluence = abs(normalized) * 100
    side = "BUY" if normalized > 0 else ("SELL" if normalized < 0 else "NEUTRAL")

    # Determine entry threshold
    base_threshold = 75.0
    if market_regime in ("STAGFLATION", "BLACK_SWAN"):
        base_threshold = 90.0
    if drawdown_pct >= 10:
        base_threshold = 85.0

    # Circuit breaker checks
    rejection_reasons = []
    if news_shield:
        rejection_reasons.append("NEWS_SHIELD_ACTIVE")
    if consecutive_losses >= 3:
        rejection_reasons.append("3_CONSECUTIVE_LOSSES")
    if daily_loss_pct >= 3.0:
        rejection_reasons.append("DAILY_LOSS_3PCT")
    if drawdown_pct >= 20:
        rejection_reasons.append("DRAWDOWN_20PCT")
    if drawdown_pct >= 30:
        rejection_reasons.append("DRAWDOWN_30PCT_HARD_STOP")
    if not mtf_aligned:
        rejection_reasons.append("MTF_NOT_ALIGNED")
    if fundamental_direction != "NEUTRAL" and fundamental_direction != side:
        rejection_reasons.append("FUNDAMENTAL_CONFLICT")

    owners_tools = ["Smart Money Concepts", "Fibonacci", "Price Action", "Moving Averages", "RSI Pro"]
    owners_agree = all(
        next((r.vote.value == side for r in school_results if r.name == t), False)
        for t in owners_tools if any(r.name == t for r in school_results)
    )
    if not owners_agree and confluence >= base_threshold:
        rejection_reasons.append("OWNER_TOOLS_CONFLICT")

    should_trade = confluence >= base_threshold and len(rejection_reasons) == 0

    sorted_breakdown = sorted(breakdown, key=lambda x: x['weight'] * x['strength'], reverse=True)
    top_factors = sorted_breakdown[:5]

    total_votes = buy_votes + sell_votes + neutral_votes
    return VoteResult(
        side=side,
        confluence_score=round(confluence, 2),
        buy_votes=buy_votes,
        sell_votes=sell_votes,
        neutral_votes=neutral_votes,
        total_votes=total_votes,
        weighted_score=round(normalized, 4),
        school_breakdown=breakdown,
        mtf_aligned=mtf_aligned,
        fundamental_aligned=(fundamental_direction == side or fundamental_direction == "NEUTRAL"),
        killzone_active=killzone_active,
        should_trade=should_trade,
        rejection_reasons=rejection_reasons,
        top_factors=top_factors,
    )
