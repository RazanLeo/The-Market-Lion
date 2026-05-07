"""Auth — register, login, 2FA, refresh, forgot/reset."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import (
    create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password, generate_totp_secret,
    totp_provisioning_uri, verify_totp, gen_token,
)
from ..db.base import get_db
from ..db.models import User, AuthSession, TradingPreference

router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=120)
    full_name: str | None = None
    preferred_lang: str = "ar"
    preferred_tz: str = "Asia/Riyadh"


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None


class TokenOut(BaseModel):
    ok: bool = True
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    twofa_enabled: bool


class TwoFAEnableOut(BaseModel):
    ok: bool = True
    secret: str
    otpauth_url: str


class TwoFAVerifyIn(BaseModel):
    code: str


# ─── Endpoints ──────────────────────────────────────────────────────
@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: RegisterIn, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    existing = (await db.execute(select(User).where(User.email == body.email.lower()))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, detail="email_taken")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        preferred_lang=body.preferred_lang,
        preferred_tz=body.preferred_tz,
        status="active",  # auto-activate; email verify wired separately
        email_verified=False,
    )
    db.add(user)
    await db.flush()
    db.add(TradingPreference(user_id=user.id))
    await db.flush()
    return await _issue_tokens(db, user, request)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = (await db.execute(select(User).where(User.email == body.email.lower()))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, detail="invalid_credentials")
    if user.status == "suspended":
        raise HTTPException(403, detail="suspended")
    if user.twofa_enabled:
        if not body.totp_code or not verify_totp(user.twofa_secret or "", body.totp_code):
            raise HTTPException(401, detail="totp_required")
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()
    return await _issue_tokens(db, user, request)


@router.post("/2fa/setup", response_model=TwoFAEnableOut)
async def twofa_setup(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    from ..deps import current_user as _cu
    user = await _cu(request.headers.get("authorization", "").replace("Bearer ", ""), db)  # type: ignore
    if user.twofa_enabled:
        raise HTTPException(409, detail="already_enabled")
    secret = generate_totp_secret()
    user.twofa_secret = secret
    await db.flush()
    return TwoFAEnableOut(secret=secret, otpauth_url=totp_provisioning_uri(secret, user.email))


@router.post("/2fa/verify")
async def twofa_verify(body: TwoFAVerifyIn, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    from ..deps import current_user as _cu
    user = await _cu(request.headers.get("authorization", "").replace("Bearer ", ""), db)  # type: ignore
    if not user.twofa_secret or not verify_totp(user.twofa_secret, body.code):
        raise HTTPException(400, detail="invalid_code")
    user.twofa_enabled = True
    await db.flush()
    return {"ok": True}


class RefreshIn(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenOut)
async def refresh_token(body: RefreshIn, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    data = decode_token(body.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(401, detail="invalid_refresh")
    h = hashlib.sha256(body.refresh_token.encode()).hexdigest()
    sess = (await db.execute(select(AuthSession).where(AuthSession.refresh_hash == h, AuthSession.revoked == False))).scalar_one_or_none()  # noqa: E712
    if not sess or sess.expires_at < datetime.now(timezone.utc):
        raise HTTPException(401, detail="refresh_expired")
    user = (await db.execute(select(User).where(User.id == data["sub"]))).scalar_one()
    sess.revoked = True
    await db.flush()
    return await _issue_tokens(db, user, request)


@router.post("/logout")
async def logout(body: RefreshIn, db: Annotated[AsyncSession, Depends(get_db)]):
    h = hashlib.sha256(body.refresh_token.encode()).hexdigest()
    sess = (await db.execute(select(AuthSession).where(AuthSession.refresh_hash == h))).scalar_one_or_none()
    if sess:
        sess.revoked = True
        await db.flush()
    return {"ok": True}


# ─── helpers ────────────────────────────────────────────────────────
async def _issue_tokens(db: AsyncSession, user: User, request: Request) -> TokenOut:
    refresh, exp = create_refresh_token(str(user.id))
    access = create_access_token(str(user.id), claims={"role": user.role, "lang": user.preferred_lang})
    h = hashlib.sha256(refresh.encode()).hexdigest()
    sess = AuthSession(
        user_id=user.id,
        refresh_hash=h,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=exp,
    )
    db.add(sess)
    await db.flush()
    return TokenOut(
        access_token=access, refresh_token=refresh, user_id=str(user.id),
        role=user.role, twofa_enabled=user.twofa_enabled,
    )
