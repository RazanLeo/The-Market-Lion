"""ORM models — mirrors Part 9 of master prompt."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Users & Auth ────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(40))
    country: Mapped[str | None] = mapped_column(String(80))
    city: Mapped[str | None] = mapped_column(String(120))
    preferred_lang: Mapped[str] = mapped_column(String(8), default="ar")
    preferred_tz: Mapped[str] = mapped_column(String(64), default="Asia/Riyadh")
    role: Mapped[str] = mapped_column(String(32), default="trader", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    twofa_secret: Mapped[str | None] = mapped_column(Text)
    twofa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    sessions: Mapped[list["AuthSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    broker_accounts: Mapped[list["BrokerAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped["TradingPreference"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    positions: Mapped[list["Position"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    refresh_hash: Mapped[str] = mapped_column(Text, nullable=False)
    ip: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    user: Mapped[User] = relationship(back_populates="sessions")


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)


# ─── Subscriptions & Payments ────────────────────────────────────
class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="SAR", nullable=False)
    features_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    payment_provider: Mapped[str | None] = mapped_column(String(32))
    external_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    user: Mapped[User] = relationship(back_populates="subscriptions")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subscriptions.id"))
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_ref: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ─── Broker links ───────────────────────────────────────────────
class BrokerAccount(Base):
    __tablename__ = "broker_accounts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    broker: Mapped[str] = mapped_column(String(32), nullable=False)  # capital | exness
    account_login: Mapped[str] = mapped_column(String(64), nullable=False)
    api_key_enc: Mapped[str] = mapped_column(Text, nullable=False)
    api_secret_enc: Mapped[str] = mapped_column(Text, nullable=False)
    account_type: Mapped[str] = mapped_column(String(16), default="demo")  # demo | live
    base_currency: Mapped[str | None] = mapped_column(String(8))
    leverage_max: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    user: Mapped[User] = relationship(back_populates="broker_accounts")


# ─── Trader prefs ───────────────────────────────────────────────
class TradingPreference(Base):
    __tablename__ = "trading_preferences"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    default_symbol: Mapped[str | None] = mapped_column(String(32))
    risk_pct: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"))
    default_tf: Mapped[str] = mapped_column(String(8), default="15M")
    reference_tf: Mapped[str] = mapped_column(String(8), default="4H")
    trade_mode: Mapped[str] = mapped_column(String(16), default="manual")
    bot_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_palette: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    toggles_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    user: Mapped[User] = relationship(back_populates="preferences")


# ─── News / Economic ────────────────────────────────────────────
class NewsItem(Base):
    __tablename__ = "news_items"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    symbols: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    sentiment: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    impact: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    category: Mapped[str | None] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class EconomicEvent(Base):
    __tablename__ = "economic_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(8))
    category: Mapped[str | None] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(Text)
    previous_v: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    forecast_v: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    actual_v: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    impact_level: Mapped[str | None] = mapped_column(String(16))
    symbols_affected: Mapped[list[str] | None] = mapped_column(ARRAY(String))


# ─── Trading ────────────────────────────────────────────────────
class TradePlan(Base):
    __tablename__ = "trade_plans"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    tf: Mapped[str] = mapped_column(String(8), nullable=False)
    entry_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    tp1_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    tp2_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    tp3_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    final_tp_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    sl_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    add_zone_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    lot_size: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    leverage: Mapped[int | None] = mapped_column(Integer)
    risk_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    risk_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    pip_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    expected_profit: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    expected_loss: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String(32), default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Position(Base):
    __tablename__ = "positions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    broker_account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("broker_accounts.id"))
    trade_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trade_plans.id"))
    broker_ticket: Mapped[str | None] = mapped_column(String(64))
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str | None] = mapped_column(String(8))
    lot_size: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    entry_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    tp_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    sl_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    trailing_sl: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    swap: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0"))
    commission: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0"))
    spread_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0"))
    pl: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0"))
    pl_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(32), default="open")
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship(back_populates="positions")


class TradeEvent(Base):
    __tablename__ = "trade_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="CASCADE"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    event: Mapped[str] = mapped_column(String(32), nullable=False)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


# ─── Audit & feature flags ──────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_role: Mapped[str | None] = mapped_column(String(32))
    action: Mapped[str | None] = mapped_column(String(64))
    resource: Mapped[str | None] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(64))
    ip: Mapped[str | None] = mapped_column(INET)
    ua: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class FeatureToggle(Base):
    __tablename__ = "feature_toggles"
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


# ─── Voting & Signals (transactional copies; hypertables done in migration) ─
class ConfluenceScoreRow(Base):
    __tablename__ = "confluence_scores"
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    tf: Mapped[str] = mapped_column(String(8), primary_key=True)
    fundamental_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    basics_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    schools_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    indicators_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    flow_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    total_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    decision: Mapped[str | None] = mapped_column(String(8))
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class SchoolSignalRow(Base):
    __tablename__ = "school_signals"
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    tf: Mapped[str] = mapped_column(String(8), primary_key=True)
    school_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    result: Mapped[str | None] = mapped_column(String(8))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    weight: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class IndicatorSignalRow(Base):
    __tablename__ = "indicator_signals"
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    tf: Mapped[str] = mapped_column(String(8), primary_key=True)
    indicator_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    result: Mapped[str | None] = mapped_column(String(8))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    weight: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
