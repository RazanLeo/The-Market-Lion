import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, JSON, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import enum


class LanguageEnum(str, enum.Enum):
    ar = "ar"
    en = "en"


class SubscriptionTierEnum(str, enum.Enum):
    free = "free"
    pro = "pro"
    vip = "vip"
    enterprise = "enterprise"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    language: Mapped[str] = mapped_column(
        SAEnum(LanguageEnum, name="language_enum", create_type=True),
        default=LanguageEnum.ar,
        nullable=False,
    )
    subscription_tier: Mapped[str] = mapped_column(
        SAEnum(SubscriptionTierEnum, name="subscription_tier_enum", create_type=True),
        default=SubscriptionTierEnum.free,
        nullable=False,
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Encrypted broker accounts stored as JSON list
    # Each entry: {"broker": str, "api_key_encrypted": str, "account_id": str, "label": str}
    broker_accounts: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} tier={self.subscription_tier}>"
