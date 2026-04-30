"""Trade model for The Market Lion."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TradeStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    PARTIAL = "PARTIAL"


class TradeType(str, Enum):
    SCALP = "SCALP"
    DAY = "DAY"
    SWING = "SWING"
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class Trade(BaseModel):
    id: Optional[str] = None
    user_id: str
    symbol: str
    side: str
    type: TradeType
    status: TradeStatus = TradeStatus.PENDING
    entry_price: float
    current_price: Optional[float] = None
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    lot_size: float
    leverage: float = 1.0
    margin_required: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    spread: float = 0.0
    pnl: float = 0.0
    pnl_percentage: float = 0.0
    risk_percentage: float = 2.0
    risk_reward: float = 3.0
    signal_id: Optional[str] = None
    confluence_score: float = 0.0
    school_signals: Dict[str, Any] = {}
    broker: str = "demo"
    broker_order_id: Optional[str] = None
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    tp1_hit_at: Optional[datetime] = None
    tp2_hit_at: Optional[datetime] = None
    close_price: Optional[float] = None
    notes: str = ""
    pyramiding_level: int = 0
    parent_trade_id: Optional[str] = None
