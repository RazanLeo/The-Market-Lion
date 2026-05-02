import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import enum


class SubscriptionStatusEnum(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tier: Mapped[str] = mapped_column(String(50), nullable=False)
    price_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    price_sar: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum(SubscriptionStatusEnum, name="subscription_status_enum", create_type=True),
        default=SubscriptionStatusEnum.active,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    user = relationship("User", backref="subscriptions", lazy="select")

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} tier={self.tier} status={self.status}>"
