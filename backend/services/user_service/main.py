"""User Service — The Market Lion.
Full CRUD: users, profiles, settings, KYC docs, subscription tiers, referral/affiliate.
PostgreSQL via asyncpg. JWT-protected endpoints. FastAPI.
"""
import asyncio
import logging
import os
import json
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

import asyncpg
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from jose import jwt, JWTError

logger = logging.getLogger("user-service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="User Service", version="1.0.0")

PG_DSN   = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/market_lion")
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production_market_lion_2025")
JWT_ALG  = "HS256"

security = HTTPBearer()


# ─── Enums ────────────────────────────────────────────────────────────────────

class PlanTier(str, Enum):
    FREE       = "free"
    STARTER    = "starter"
    PRO        = "pro"
    VIP        = "vip"
    ENTERPRISE = "enterprise"


class KYCStatus(str, Enum):
    NOT_SUBMITTED = "not_submitted"
    PENDING       = "pending"
    APPROVED      = "approved"
    REJECTED      = "rejected"


class UserStatus(str, Enum):
    ACTIVE    = "active"
    SUSPENDED = "suspended"
    DELETED   = "deleted"
    UNVERIFIED = "unverified"


class NotificationChannel(str, Enum):
    TELEGRAM = "telegram"
    EMAIL    = "email"
    PUSH     = "push"
    DISCORD  = "discord"


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class UserCreateRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    referral_code: Optional[str] = None

    @validator('username')
    def username_valid(cls, v):
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError("Username: only letters, digits, _ and . allowed")
        return v.lower()

    @validator('password')
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None


class UserSettingsRequest(BaseModel):
    default_risk_pct: Optional[float] = None
    default_timeframe: Optional[str] = None
    default_symbols: Optional[List[str]] = None
    notification_channels: Optional[List[str]] = None
    notification_min_confidence: Optional[float] = None
    telegram_chat_id: Optional[str] = None
    discord_webhook: Optional[str] = None
    theme: Optional[str] = None           # dark/light
    language: Optional[str] = None        # ar/en
    chart_type: Optional[str] = None
    show_fundamentals: Optional[bool] = None
    show_ml_score: Optional[bool] = None
    auto_trading: Optional[bool] = None
    auto_trading_max_lots: Optional[float] = None
    broker_id: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def pw_strong(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class KYCSubmitRequest(BaseModel):
    document_type: str   # passport / national_id / driving_license
    document_number: str
    full_name: str
    date_of_birth: str   # YYYY-MM-DD
    country: str


# ─── DB Connection Pool ───────────────────────────────────────────────────────

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(PG_DSN, min_size=2, max_size=10)
    return _pool


# ─── Auth Helpers ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = "market_lion_2025"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


def decode_token(token: str) -> Dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Invalid token payload")
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id=$1 AND status='active'", int(user_id))
    if not row:
        raise HTTPException(401, "User not found or inactive")
    return dict(row)


async def require_admin(user: Dict = Depends(get_current_user)) -> Dict:
    if not user.get("is_admin"):
        raise HTTPException(403, "Admin required")
    return user


# ─── Plan Permissions ─────────────────────────────────────────────────────────

PLAN_LIMITS = {
    PlanTier.FREE:       {"max_symbols": 3,  "max_alerts": 3,  "signals_per_day": 5,  "ml_access": False, "api_access": False},
    PlanTier.STARTER:    {"max_symbols": 5,  "max_alerts": 10, "signals_per_day": 20, "ml_access": False, "api_access": False},
    PlanTier.PRO:        {"max_symbols": 15, "max_alerts": 50, "signals_per_day": 100,"ml_access": True,  "api_access": False},
    PlanTier.VIP:        {"max_symbols": 30, "max_alerts": 200,"signals_per_day": 500,"ml_access": True,  "api_access": True},
    PlanTier.ENTERPRISE: {"max_symbols": 999,"max_alerts": 999,"signals_per_day": 999,"ml_access": True,  "api_access": True},
}


# ─── DB Schema Initialization ─────────────────────────────────────────────────

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(30) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL,
    full_name VARCHAR(200),
    phone VARCHAR(30),
    country VARCHAR(100),
    bio TEXT DEFAULT '',
    avatar_url TEXT,
    preferred_language VARCHAR(10) DEFAULT 'ar',
    timezone VARCHAR(60) DEFAULT 'UTC',
    is_admin BOOLEAN DEFAULT FALSE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    email_verify_token VARCHAR(64),
    reset_token VARCHAR(64),
    reset_token_expires TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'unverified',
    plan VARCHAR(20) DEFAULT 'free',
    plan_expires_at TIMESTAMPTZ,
    referral_code VARCHAR(16) UNIQUE,
    referred_by INT REFERENCES users(id),
    affiliate_earnings DECIMAL(12,2) DEFAULT 0,
    total_referrals INT DEFAULT 0,
    signal_count_today INT DEFAULT 0,
    signal_count_reset_at DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_risk_pct DECIMAL(5,2) DEFAULT 2.0,
    default_timeframe VARCHAR(10) DEFAULT 'H1',
    default_symbols TEXT[] DEFAULT ARRAY['XAUUSD','EURUSD'],
    notification_channels TEXT[] DEFAULT ARRAY['email'],
    notification_min_confidence DECIMAL(4,3) DEFAULT 0.75,
    telegram_chat_id VARCHAR(50),
    discord_webhook TEXT,
    theme VARCHAR(10) DEFAULT 'dark',
    language VARCHAR(5) DEFAULT 'ar',
    chart_type VARCHAR(20) DEFAULT 'candlestick',
    show_fundamentals BOOLEAN DEFAULT TRUE,
    show_ml_score BOOLEAN DEFAULT TRUE,
    auto_trading BOOLEAN DEFAULT FALSE,
    auto_trading_max_lots DECIMAL(8,2) DEFAULT 0.01,
    broker_id VARCHAR(50),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kyc_documents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(50),
    document_number VARCHAR(100),
    full_name VARCHAR(200),
    date_of_birth DATE,
    country VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    rejection_reason TEXT,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by BIGINT
);

CREATE TABLE IF NOT EXISTS user_activity_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100),
    ip_address VARCHAR(50),
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watchlists (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    symbols TEXT[],
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_alerts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    asset VARCHAR(20),
    condition VARCHAR(50),   -- price_above, price_below, signal_buy, signal_sell
    value DECIMAL(18,8),
    timeframe VARCHAR(10),
    channel VARCHAR(20) DEFAULT 'telegram',
    active BOOLEAN DEFAULT TRUE,
    triggered_count INT DEFAULT 0,
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON user_alerts(user_id);
"""


async def ensure_tables():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLES_SQL)
    logger.info("User-service tables ensured")


def generate_referral_code() -> str:
    return secrets.token_hex(6).upper()


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    await ensure_tables()
    logger.info("User service started")


@app.on_event("shutdown")
async def shutdown():
    global _pool
    if _pool:
        await _pool.close()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "user-service"}


# ── User CRUD ─────────────────────────────────────────────────────────────────

@app.post("/users", status_code=201)
async def create_user(req: UserCreateRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check uniqueness
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email=$1 OR username=$2", req.email.lower(), req.username
        )
        if existing:
            raise HTTPException(409, "Email or username already registered")

        ref_code = generate_referral_code()
        referred_by = None
        if req.referral_code:
            ref_row = await conn.fetchrow("SELECT id FROM users WHERE referral_code=$1", req.referral_code.upper())
            if ref_row:
                referred_by = ref_row["id"]

        verify_token = secrets.token_hex(32)
        pw_hash = hash_password(req.password)

        user = await conn.fetchrow(
            """INSERT INTO users (email, username, password_hash, full_name, phone, country,
               referral_code, referred_by, email_verify_token, status)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,'unverified') RETURNING *""",
            req.email.lower(), req.username, pw_hash,
            req.full_name, req.phone, req.country,
            ref_code, referred_by, verify_token,
        )
        user_id = user["id"]

        # Create default settings
        await conn.execute(
            "INSERT INTO user_settings (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id
        )

        # Create default watchlist
        await conn.execute(
            """INSERT INTO watchlists (user_id, name, symbols, is_default)
               VALUES ($1, 'My Watchlist', $2, TRUE)""",
            user_id, ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSD"],
        )

        # Update referrer count
        if referred_by:
            await conn.execute("UPDATE users SET total_referrals = total_referrals + 1 WHERE id=$1", referred_by)

    return {
        "id": user_id, "email": req.email.lower(), "username": req.username,
        "referral_code": ref_code, "verify_token": verify_token,
        "message": "User created. Please verify your email.",
    }


@app.get("/users/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        settings = await conn.fetchrow("SELECT * FROM user_settings WHERE user_id=$1", current_user["id"])
        kyc = await conn.fetchrow(
            "SELECT status, document_type FROM kyc_documents WHERE user_id=$1 ORDER BY submitted_at DESC LIMIT 1",
            current_user["id"]
        )
    plan = current_user.get("plan", "free")
    limits = PLAN_LIMITS.get(PlanTier(plan), PLAN_LIMITS[PlanTier.FREE])
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "username": current_user["username"],
        "full_name": current_user.get("full_name"),
        "country": current_user.get("country"),
        "avatar_url": current_user.get("avatar_url"),
        "plan": plan,
        "plan_expires_at": current_user.get("plan_expires_at"),
        "status": current_user.get("status"),
        "is_email_verified": current_user.get("is_email_verified"),
        "preferred_language": current_user.get("preferred_language", "ar"),
        "timezone": current_user.get("timezone", "UTC"),
        "referral_code": current_user.get("referral_code"),
        "total_referrals": current_user.get("total_referrals", 0),
        "affiliate_earnings": float(current_user.get("affiliate_earnings", 0)),
        "last_login": current_user.get("last_login"),
        "created_at": current_user.get("created_at"),
        "settings": dict(settings) if settings else {},
        "kyc_status": kyc["status"] if kyc else KYCStatus.NOT_SUBMITTED,
        "plan_limits": limits,
    }


@app.put("/users/me")
async def update_me(req: UserUpdateRequest, current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    updates = {k: v for k, v in req.dict().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    updates["updated_at"] = datetime.now(timezone.utc)
    set_clause = ", ".join(f"{k}=${i+1}" for i, k in enumerate(updates))
    values = list(updates.values()) + [current_user["id"]]
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE users SET {set_clause} WHERE id=${len(values)}",
            *values
        )
    return {"status": "updated"}


@app.get("/users/{user_id}")
async def get_user_by_id(user_id: int, admin: Dict = Depends(require_admin)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not row:
        raise HTTPException(404, "User not found")
    return dict(row)


@app.delete("/users/me")
async def delete_me(current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET status='deleted', updated_at=NOW() WHERE id=$1", current_user["id"])
    return {"status": "account_deleted"}


# ── Settings ──────────────────────────────────────────────────────────────────

@app.get("/users/me/settings")
async def get_settings(current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM user_settings WHERE user_id=$1", current_user["id"])
    if not row:
        raise HTTPException(404, "Settings not found")
    return dict(row)


@app.put("/users/me/settings")
async def update_settings(req: UserSettingsRequest, current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    updates = {k: v for k, v in req.dict().items() if v is not None}
    if not updates:
        return {"status": "no_changes"}
    updates["updated_at"] = datetime.now(timezone.utc)
    set_clause = ", ".join(f"{k}=${i+1}" for i, k in enumerate(updates))
    values = list(updates.values()) + [current_user["id"]]
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE user_settings SET {set_clause} WHERE user_id=${len(values)}",
            *values
        )
    return {"status": "settings_updated"}


# ── Password ──────────────────────────────────────────────────────────────────

@app.post("/users/me/password")
async def change_password(req: ChangePasswordRequest, current_user: Dict = Depends(get_current_user)):
    if not verify_password(req.current_password, current_user["password_hash"]):
        raise HTTPException(400, "Current password incorrect")
    new_hash = hash_password(req.new_password)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET password_hash=$1, updated_at=NOW() WHERE id=$2", new_hash, current_user["id"])
    return {"status": "password_changed"}


@app.post("/auth/forgot-password")
async def forgot_password(email: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE email=$1", email.lower())
        if user:
            token = secrets.token_hex(32)
            expires = datetime.now(timezone.utc) + timedelta(hours=2)
            await conn.execute(
                "UPDATE users SET reset_token=$1, reset_token_expires=$2 WHERE id=$3",
                token, expires, user["id"]
            )
            # In production: send email. Here: return token for testing.
            return {"status": "reset_email_sent", "debug_token": token}
    return {"status": "reset_email_sent"}  # don't leak whether email exists


@app.post("/auth/reset-password")
async def reset_password(token: str, new_password: str):
    if len(new_password) < 8:
        raise HTTPException(400, "Password too short")
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id FROM users WHERE reset_token=$1 AND reset_token_expires > NOW()", token
        )
        if not user:
            raise HTTPException(400, "Invalid or expired reset token")
        new_hash = hash_password(new_password)
        await conn.execute(
            "UPDATE users SET password_hash=$1, reset_token=NULL, reset_token_expires=NULL, updated_at=NOW() WHERE id=$2",
            new_hash, user["id"]
        )
    return {"status": "password_reset_successful"}


@app.post("/auth/verify-email")
async def verify_email(token: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE email_verify_token=$1", token)
        if not user:
            raise HTTPException(400, "Invalid verification token")
        await conn.execute(
            "UPDATE users SET is_email_verified=TRUE, status='active', email_verify_token=NULL WHERE id=$1",
            user["id"]
        )
    return {"status": "email_verified"}


# ── KYC ───────────────────────────────────────────────────────────────────────

@app.post("/users/me/kyc")
async def submit_kyc(req: KYCSubmitRequest, current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, status FROM kyc_documents WHERE user_id=$1 AND status='approved'",
            current_user["id"]
        )
        if existing:
            raise HTTPException(400, "KYC already approved")

        try:
            dob = datetime.strptime(req.date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, "Invalid date format, use YYYY-MM-DD")

        kyc_id = await conn.fetchval(
            """INSERT INTO kyc_documents
               (user_id, document_type, document_number, full_name, date_of_birth, country, status)
               VALUES ($1,$2,$3,$4,$5,$6,'pending') RETURNING id""",
            current_user["id"], req.document_type, req.document_number,
            req.full_name, dob, req.country,
        )
    return {"kyc_id": kyc_id, "status": "pending", "message": "KYC submitted for review"}


@app.get("/users/me/kyc")
async def get_kyc(current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, document_type, status, submitted_at, reviewed_at FROM kyc_documents WHERE user_id=$1 ORDER BY submitted_at DESC",
            current_user["id"]
        )
    return {"kyc_submissions": [dict(r) for r in rows]}


@app.put("/admin/kyc/{kyc_id}")
async def review_kyc(kyc_id: int, status: str, rejection_reason: Optional[str] = None, admin: Dict = Depends(require_admin)):
    if status not in ("approved", "rejected"):
        raise HTTPException(400, "Status must be approved or rejected")
    pool = await get_pool()
    async with pool.acquire() as conn:
        kyc = await conn.fetchrow("SELECT user_id FROM kyc_documents WHERE id=$1", kyc_id)
        if not kyc:
            raise HTTPException(404, "KYC not found")
        await conn.execute(
            "UPDATE kyc_documents SET status=$1, rejection_reason=$2, reviewed_at=NOW(), reviewed_by=$3 WHERE id=$4",
            status, rejection_reason, admin["id"], kyc_id,
        )
    return {"kyc_id": kyc_id, "status": status}


# ── Watchlists ────────────────────────────────────────────────────────────────

@app.get("/users/me/watchlists")
async def get_watchlists(current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM watchlists WHERE user_id=$1", current_user["id"])
    return {"watchlists": [dict(r) for r in rows]}


@app.post("/users/me/watchlists")
async def create_watchlist(name: str, symbols: List[str], current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        wl_id = await conn.fetchval(
            "INSERT INTO watchlists (user_id, name, symbols) VALUES ($1,$2,$3) RETURNING id",
            current_user["id"], name, symbols,
        )
    return {"id": wl_id, "name": name, "symbols": symbols}


@app.put("/users/me/watchlists/{wl_id}")
async def update_watchlist(wl_id: int, symbols: List[str], name: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        wl = await conn.fetchrow("SELECT id FROM watchlists WHERE id=$1 AND user_id=$2", wl_id, current_user["id"])
        if not wl:
            raise HTTPException(404, "Watchlist not found")
        if name:
            await conn.execute("UPDATE watchlists SET name=$1, symbols=$2 WHERE id=$3", name, symbols, wl_id)
        else:
            await conn.execute("UPDATE watchlists SET symbols=$1 WHERE id=$2", symbols, wl_id)
    return {"status": "updated"}


@app.delete("/users/me/watchlists/{wl_id}")
async def delete_watchlist(wl_id: int, current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM watchlists WHERE id=$1 AND user_id=$2 AND is_default=FALSE", wl_id, current_user["id"])
    return {"status": "deleted"}


# ── Alerts ────────────────────────────────────────────────────────────────────

@app.get("/users/me/alerts")
async def get_alerts(current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM user_alerts WHERE user_id=$1 ORDER BY created_at DESC", current_user["id"])
    return {"alerts": [dict(r) for r in rows]}


@app.post("/users/me/alerts")
async def create_alert(
    asset: str, condition: str, value: float, timeframe: str = "H1",
    channel: str = "telegram", current_user: Dict = Depends(get_current_user)
):
    plan = current_user.get("plan", "free")
    limits = PLAN_LIMITS.get(PlanTier(plan), PLAN_LIMITS[PlanTier.FREE])
    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM user_alerts WHERE user_id=$1 AND active=TRUE", current_user["id"])
        if count >= limits["max_alerts"]:
            raise HTTPException(403, f"Alert limit reached for {plan} plan ({limits['max_alerts']} max)")
        alert_id = await conn.fetchval(
            """INSERT INTO user_alerts (user_id, asset, condition, value, timeframe, channel)
               VALUES ($1,$2,$3,$4,$5,$6) RETURNING id""",
            current_user["id"], asset.upper(), condition, value, timeframe.upper(), channel,
        )
    return {"id": alert_id, "status": "created"}


@app.delete("/users/me/alerts/{alert_id}")
async def delete_alert(alert_id: int, current_user: Dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE user_alerts SET active=FALSE WHERE id=$1 AND user_id=$2", alert_id, current_user["id"])
    return {"status": "alert_deactivated"}


# ── Admin endpoints ───────────────────────────────────────────────────────────

@app.get("/admin/users")
async def list_users(page: int = 1, limit: int = 50, admin: Dict = Depends(require_admin)):
    offset = (page - 1) * limit
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, email, username, plan, status, is_email_verified, created_at FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, offset,
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
    return {"users": [dict(r) for r in rows], "total": total, "page": page, "limit": limit}


@app.put("/admin/users/{user_id}/plan")
async def update_user_plan(user_id: int, plan: str, expires_at: Optional[str] = None, admin: Dict = Depends(require_admin)):
    if plan not in [p.value for p in PlanTier]:
        raise HTTPException(400, "Invalid plan tier")
    pool = await get_pool()
    exp = datetime.fromisoformat(expires_at) if expires_at else None
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET plan=$1, plan_expires_at=$2 WHERE id=$3", plan, exp, user_id)
    return {"status": "plan_updated", "user_id": user_id, "plan": plan}


@app.put("/admin/users/{user_id}/status")
async def update_user_status(user_id: int, status: str, admin: Dict = Depends(require_admin)):
    if status not in [s.value for s in UserStatus]:
        raise HTTPException(400, "Invalid status")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET status=$1 WHERE id=$2", status, user_id)
    return {"status": "updated"}


@app.get("/admin/stats")
async def admin_stats(admin: Dict = Depends(require_admin)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        active = await conn.fetchval("SELECT COUNT(*) FROM users WHERE status='active'")
        pro = await conn.fetchval("SELECT COUNT(*) FROM users WHERE plan='pro'")
        vip = await conn.fetchval("SELECT COUNT(*) FROM users WHERE plan='vip'")
        kyc_pending = await conn.fetchval("SELECT COUNT(*) FROM users WHERE kyc_status='pending'")
        referrals = await conn.fetchval("SELECT COALESCE(SUM(total_referrals),0) FROM users")
        by_plan = await conn.fetch("SELECT plan, COUNT(*) as count FROM users GROUP BY plan")
        by_status = await conn.fetch("SELECT status, COUNT(*) as count FROM users GROUP BY status")
        today = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '1 day'")
        this_week = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'")
    return {
        "total_users": total,
        "active_users": active,
        "pro_users": pro,
        "vip_users": vip,
        "kyc_pending": kyc_pending,
        "total_referrals": referrals,
        "new_today": today,
        "new_this_week": this_week,
        "by_plan": {r["plan"]: r["count"] for r in by_plan},
        "by_status": {r["status"]: r["count"] for r in by_status},
    }


@app.put("/admin/users/{user_id}/kyc")
async def admin_update_kyc(user_id: int, status: str, notes: Optional[str] = None, admin: Dict = Depends(require_admin)):
    """Approve or reject KYC from admin panel."""
    if status not in ("approved", "rejected", "pending"):
        raise HTTPException(400, "Invalid KYC status")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET kyc_status=$1, kyc_notes=$2, kyc_reviewed_at=NOW(), kyc_reviewed_by=$3 WHERE id=$4",
            status, notes, admin.get("user_id"), user_id
        )
    return {"status": "kyc_updated", "user_id": user_id, "kyc_status": status}


@app.get("/admin/users/{user_id}/activity")
async def admin_user_activity(user_id: int, limit: int = 50, admin: Dict = Depends(require_admin)):
    """Get activity log for a specific user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT action, details, ip_address, created_at FROM user_activity_log WHERE user_id=$1 ORDER BY created_at DESC LIMIT $2",
            user_id, min(limit, 200)
        )
    return {"user_id": user_id, "activity": [dict(r) for r in rows]}


@app.post("/admin/broadcast")
async def admin_broadcast(message: str, plan_filter: Optional[str] = None, admin: Dict = Depends(require_admin)):
    """Push a notification/message to all (or filtered) users via Redis queue."""
    import redis.asyncio as aioredis
    r = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        if plan_filter:
            users = await conn.fetch("SELECT id, email FROM users WHERE plan=$1 AND status='active'", plan_filter)
        else:
            users = await conn.fetch("SELECT id, email FROM users WHERE status='active'")

    import json
    broadcast_msg = {"type": "admin_broadcast", "message": message, "sent_at": datetime.now(timezone.utc).isoformat()}
    await r.lpush("admin_broadcast_queue", json.dumps(broadcast_msg))
    return {"status": "queued", "target_users": len(users), "plan_filter": plan_filter}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=False)
