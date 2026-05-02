"""Market Lion — Auth Service (FastAPI) — JWT + 2FA + Sessions."""
import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg
import redis.asyncio as aioredis
import pyotp
import qrcode
import io
import base64
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth-service")

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_in_production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = 60 * 15            # 15 minutes
REFRESH_TOKEN_TTL = 60 * 60 * 24 * 7  # 7 days (spec requirement)
SESSION_IDLE_TTL = 60 * 30            # 30 min idle session expiry

# Argon2id — spec section 14.1 requirement
# Falls back to bcrypt if argon2-cffi not installed
try:
    pwd_ctx = CryptContext(
        schemes=["argon2"],
        deprecated="auto",
        argon2__memory_cost=65536,   # 64 MB
        argon2__time_cost=3,
        argon2__parallelism=4,
        argon2__hash_len=32,
        argon2__type="ID",
    )
    _HASH_SCHEME = "argon2"
except Exception:
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _HASH_SCHEME = "bcrypt"
    logger.warning("argon2-cffi not available — falling back to bcrypt. Install argon2-cffi for Argon2id.")

app = FastAPI(title="Market Lion Auth", version="1.0.0", docs_url="/auth/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ──────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────
_pool: Optional[asyncpg.Pool] = None
_redis: Optional[aioredis.Redis] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(os.getenv("POSTGRES_URL", "postgresql://lion:lion_secret_2024@localhost:5432/market_lion"))
    return _pool


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/1"), decode_responses=True)
    return _redis


# ──────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: str = "SA"
    language: str = "ar"
    referral_code: Optional[str] = None

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("كلمة المرور يجب أن تكون 8 أحرف على الأقل")
        if not any(c.isupper() for c in v):
            raise ValueError("يجب أن تحتوي على حرف كبير")
        if not any(c.isdigit() for c in v):
            raise ValueError("يجب أن تحتوي على رقم")
        return v

    @validator("username")
    def username_valid(cls, v):
        if len(v) < 3 or len(v) > 30:
            raise ValueError("اسم المستخدم بين 3-30 حرف")
        if not v.replace("_", "").isalnum():
            raise ValueError("اسم المستخدم يحتوي على أحرف وأرقام فقط")
        return v.lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None
    device_info: Optional[dict] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class Enable2FARequest(BaseModel):
    totp_code: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ──────────────────────────────────────────────
# Token helpers
# ──────────────────────────────────────────────
def create_access_token(user_id: str, plan: str = "free") -> str:
    payload = {
        "sub": user_id,
        "plan": plan,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_TTL),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": secrets.token_hex(16),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_TTL),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")


# ──────────────────────────────────────────────
# Startup
# ──────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await get_pool()
    await get_redis()
    logger.info("Auth service started")


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
@app.post("/auth/register")
async def register(req: RegisterRequest, request: Request):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check email/username uniqueness
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email=$1 OR username=$2",
            req.email, req.username
        )
        if existing:
            raise HTTPException(status_code=409, detail="البريد الإلكتروني أو اسم المستخدم مستخدم بالفعل")

        referred_by = None
        if req.referral_code:
            ref = await conn.fetchrow("SELECT id FROM users WHERE referral_code=$1", req.referral_code)
            if ref:
                referred_by = ref["id"]

        password_hash = pwd_ctx.hash(req.password)
        user = await conn.fetchrow(
            """INSERT INTO users (email, username, password_hash, full_name, phone, country, language, referred_by)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id, referral_code""",
            req.email, req.username, password_hash, req.full_name,
            req.phone, req.country, req.language, referred_by
        )

        # Create free subscription
        await conn.execute(
            "INSERT INTO subscriptions (user_id, plan_id, billing_cycle) VALUES ($1, 1, 'monthly')",
            user["id"]
        )

    access_token = create_access_token(str(user["id"]))
    refresh_token = create_refresh_token(str(user["id"]))

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions (user_id, refresh_token, ip_address, expires_at) VALUES ($1,$2,$3,NOW()+INTERVAL '30 days')",
            user["id"], hashlib.sha256(refresh_token.encode()).hexdigest(),
            request.client.host if request.client else None
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"id": str(user["id"]), "email": req.email, "username": req.username, "plan": "free"}
    }


@app.post("/auth/login")
async def login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    redis = await get_redis()

    # Rate limit: max 5 failed attempts → lockout 15 min (spec 14.1)
    fail_key = f"login_fail:{client_ip}:{req.email}"
    fail_count = int(await redis.get(fail_key) or 0)
    if fail_count >= 5:
        ttl = await redis.ttl(fail_key)
        raise HTTPException(
            status_code=429,
            detail=f"حساب مقفل مؤقتاً بسبب محاولات خاطئة. انتظر {ttl} ثانية",
        )

    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            """SELECT u.id, u.email, u.username, u.password_hash, u.is_active,
                      u.is_2fa_enabled, u.totp_secret, p.name as plan
               FROM users u
               LEFT JOIN subscriptions s ON s.user_id = u.id AND s.status='active'
               LEFT JOIN plans p ON p.id = s.plan_id
               WHERE u.email=$1 AND u.deleted_at IS NULL""",
            req.email
        )
        if not user or not pwd_ctx.verify(req.password, user["password_hash"]):
            # Increment fail counter, expire after 15 minutes
            await redis.incr(fail_key)
            await redis.expire(fail_key, 900)
            remaining = 5 - int(await redis.get(fail_key) or 1)
            detail = f"بيانات الدخول غير صحيحة. محاولات متبقية: {max(0, remaining)}"
            if remaining <= 0:
                detail = "تم قفل الحساب مؤقتاً (5 محاولات خاطئة). انتظر 15 دقيقة"
            raise HTTPException(status_code=401, detail=detail)

        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="الحساب موقوف")

        # Clear fail counter on success
        await redis.delete(fail_key)

        if user["is_2fa_enabled"]:
            if not req.totp_code:
                return JSONResponse({"requires_2fa": True, "message": "أدخل رمز التحقق الثنائي"}, status_code=200)
            totp = pyotp.TOTP(user["totp_secret"])
            if not totp.verify(req.totp_code, valid_window=1):
                raise HTTPException(status_code=401, detail="رمز التحقق خاطئ")

        await conn.execute("UPDATE users SET last_login=NOW() WHERE id=$1", user["id"])

    access_token = create_access_token(str(user["id"]), user["plan"] or "free")
    refresh_token = create_refresh_token(str(user["id"]))

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions (user_id, refresh_token, device_info, ip_address, expires_at) VALUES ($1,$2,$3,$4,NOW()+INTERVAL '30 days')",
            user["id"], hashlib.sha256(refresh_token.encode()).hexdigest(),
            req.device_info or {}, request.client.host if request.client else None
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"id": str(user["id"]), "email": user["email"], "username": user["username"], "plan": user["plan"] or "free"}
    }


@app.post("/auth/refresh")
async def refresh_token(req: RefreshRequest):
    try:
        payload = jwt.decode(req.refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired")

    token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()
    pool = await get_pool()
    async with pool.acquire() as conn:
        session = await conn.fetchrow(
            "SELECT id, user_id FROM sessions WHERE refresh_token=$1 AND revoked_at IS NULL AND expires_at > NOW()",
            token_hash
        )
        if not session:
            raise HTTPException(status_code=401, detail="Session not found or revoked")

        user = await conn.fetchrow(
            "SELECT u.id, p.name as plan FROM users u LEFT JOIN subscriptions s ON s.user_id=u.id AND s.status='active' LEFT JOIN plans p ON p.id=s.plan_id WHERE u.id=$1",
            session["user_id"]
        )

    new_access = create_access_token(str(user["id"]), user["plan"] or "free")
    return {"access_token": new_access, "token_type": "bearer"}


@app.post("/auth/logout")
async def logout(req: RefreshRequest):
    token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE sessions SET revoked_at=NOW() WHERE refresh_token=$1", token_hash
        )
    return {"message": "تم تسجيل الخروج بنجاح"}


@app.post("/auth/2fa/setup")
async def setup_2fa(current_user=Depends(get_current_user)):
    user_id = current_user["sub"]
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT email, username FROM users WHERE id=$1", user_id)

    totp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret)
    provisioning_uri = totp.provisioning_uri(name=user["email"], issuer_name="أسد السوق")

    # Generate QR code as base64
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    redis = await get_redis()
    await redis.setex(f"2fa_setup:{user_id}", 300, totp_secret)

    return {
        "secret": totp_secret,
        "qr_code": f"data:image/png;base64,{qr_b64}",
        "provisioning_uri": provisioning_uri,
        "message": "امسح رمز QR بتطبيق المصادقة ثم أدخل الرمز للتأكيد"
    }


@app.post("/auth/2fa/enable")
async def enable_2fa(req: Enable2FARequest, current_user=Depends(get_current_user)):
    user_id = current_user["sub"]
    redis = await get_redis()
    totp_secret = await redis.get(f"2fa_setup:{user_id}")
    if not totp_secret:
        raise HTTPException(status_code=400, detail="انتهت صلاحية الإعداد، أعد المحاولة")

    totp = pyotp.TOTP(totp_secret)
    if not totp.verify(req.totp_code, valid_window=1):
        raise HTTPException(status_code=400, detail="رمز التحقق خاطئ")

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_2fa_enabled=TRUE, totp_secret=$1 WHERE id=$2",
            totp_secret, user_id
        )

    await redis.delete(f"2fa_setup:{user_id}")
    return {"message": "تم تفعيل التحقق الثنائي بنجاح", "backup_codes": [secrets.token_hex(4).upper() for _ in range(8)]}


@app.post("/auth/2fa/disable")
async def disable_2fa(req: Enable2FARequest, current_user=Depends(get_current_user)):
    user_id = current_user["sub"]
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT totp_secret FROM users WHERE id=$1", user_id)
        if not user["totp_secret"]:
            raise HTTPException(status_code=400, detail="2FA غير مفعل")
        totp = pyotp.TOTP(user["totp_secret"])
        if not totp.verify(req.totp_code, valid_window=1):
            raise HTTPException(status_code=400, detail="رمز التحقق خاطئ")
        await conn.execute("UPDATE users SET is_2fa_enabled=FALSE, totp_secret=NULL WHERE id=$1", user_id)
    return {"message": "تم إيقاف التحقق الثنائي"}


@app.get("/auth/me")
async def get_me(current_user=Depends(get_current_user)):
    user_id = current_user["sub"]
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            """SELECT u.id, u.email, u.username, u.full_name, u.phone, u.country, u.language,
                      u.avatar_url, u.is_verified, u.is_2fa_enabled, u.kyc_status, u.kyc_level,
                      u.referral_code, u.created_at, p.name as plan, s.ends_at as plan_expires
               FROM users u
               LEFT JOIN subscriptions s ON s.user_id=u.id AND s.status='active'
               LEFT JOIN plans p ON p.id=s.plan_id
               WHERE u.id=$1""",
            user_id
        )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)


@app.post("/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE email=$1", req.email)

    if user:
        token = secrets.token_urlsafe(32)
        redis = await get_redis()
        await redis.setex(f"pwd_reset:{token}", 3600, str(user["id"]))
        logger.info(f"Password reset token for {req.email}: {token}")
        # TODO: Send email via SendGrid

    # Always return same message to prevent email enumeration
    return {"message": "إذا كان البريد صحيحاً، ستصلك رسالة لإعادة تعيين كلمة المرور"}


@app.post("/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    redis = await get_redis()
    user_id = await redis.get(f"pwd_reset:{req.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="رابط إعادة التعيين منتهي الصلاحية أو غير صالح")

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET password_hash=$1 WHERE id=$2",
            pwd_ctx.hash(req.new_password), user_id
        )
        # Revoke all sessions
        await conn.execute("UPDATE sessions SET revoked_at=NOW() WHERE user_id=$1", user_id)

    await redis.delete(f"pwd_reset:{req.token}")
    return {"message": "تم تغيير كلمة المرور بنجاح"}


@app.get("/auth/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
