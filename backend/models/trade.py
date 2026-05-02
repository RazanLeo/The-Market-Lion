import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import enum


class BrokerEnum(str, enum.Enum):
    capital_com = "capital_com"
    exness = "exness"
    mt5 = "mt5"


class TradeSideEnum(str, enum.Enum):
    buy = "buy"
    sell = "sell"


class TradeStatusEnum(str, enum.Enum):
    pending = "pending"
    open = "open"
    closed = "closed"
    cancelled = "cancelled"


class SignalSourceEnum(str, enum.Enum):
    bot = "bot"
    manual = "manual"


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    broker: Mapped[str] = mapped_column(
        SAEnum(BrokerEnum, name="broker_enum", create_type=True),
        nullable=False,
    )
    side: Mapped[str] = mapped_column(
        SAEnum(TradeSideEnum, name="trade_side_enum", create_type=True),
        nullable=False,
    )

    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit_1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit_2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit_3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    lot_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum(TradeStatusEnum, name="trade_status_enum", create_type=True),
        default=TradeStatusEnum.pending,
        nullable=False,
        index=True,
    )

    pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confluence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    signal_source: Mapped[str] = mapped_column(
        SAEnum(SignalSourceEnum, name="signal_source_enum", create_type=True),
        default=SignalSourceEnum.manual,
        nullable=False,
    )

    open_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    close_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    broker_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    user = relationship("User", backref="trades", lazy="select")

    def __repr__(self) -> str:
        return f"<Trade id={self.id} symbol={self.symbol} side={self.side} status={self.status}>"
