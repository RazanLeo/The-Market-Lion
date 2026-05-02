"""Market state models for The Market Lion."""
from enum import Enum
from typing import Optional, Dict, List
from pydantic import BaseModel
from datetime import datetime


class MarketRegime(str, Enum):
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    STAGFLATION = "STAGFLATION"
    RECESSION_FEAR = "RECESSION_FEAR"
    NEUTRAL = "NEUTRAL"
    BLACK_SWAN = "BLACK_SWAN"


class TimeFrame(str, Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN = "MN"


class OHLCV(BaseModel):
    symbol: str
    timeframe: TimeFrame
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime


class KillZone(str, Enum):
    ASIAN = "ASIAN"
    LONDON_OPEN = "LONDON_OPEN"
    NY_OPEN = "NY_OPEN"
    LONDON_CLOSE = "LONDON_CLOSE"
    NY_PM = "NY_PM"
    OFF_HOURS = "OFF_HOURS"


KILLZONE_HOURS = {
    KillZone.ASIAN: (0, 6),
    KillZone.LONDON_OPEN: (7, 10),
    KillZone.NY_OPEN: (12, 15),
    KillZone.LONDON_CLOSE: (15, 17),
    KillZone.NY_PM: (18, 20),
}


class MarketState(BaseModel):
    symbol: str
    regime: MarketRegime = MarketRegime.NEUTRAL
    current_killzone: KillZone = KillZone.OFF_HOURS
    is_trending: bool = False
    trend_direction: str = "NEUTRAL"
    volatility_level: str = "NORMAL"
    atr_current: float = 0.0
    atr_average: float = 0.0
    vix_level: Optional[float] = None
    dxy_direction: str = "NEUTRAL"
    updated_at: datetime = None
