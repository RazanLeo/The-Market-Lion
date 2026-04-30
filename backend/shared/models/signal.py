"""Signal model for The Market Lion."""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class SignalSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


class SignalStrength(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


class SchoolVote(BaseModel):
    school_name: str
    side: SignalSide
    strength: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    details: Dict[str, Any] = {}


class Signal(BaseModel):
    id: Optional[str] = None
    symbol: str
    timeframe: str
    side: SignalSide
    confluence_score: float = Field(ge=0.0, le=100.0)
    strength: SignalStrength
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    lot_size: float
    risk_percentage: float
    risk_reward_1: float
    risk_reward_2: float
    risk_reward_3: float
    fundamental_score: float = Field(ge=0.0, le=100.0)
    technical_score: float = Field(ge=0.0, le=100.0)
    liquidity_score: float = Field(ge=0.0, le=100.0)
    school_votes: List[SchoolVote] = []
    mtf_alignment: bool = False
    killzone_active: bool = False
    news_shield_active: bool = False
    market_regime: str = "NEUTRAL"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    explanation: str = ""
    top_factors: List[Dict[str, Any]] = []
