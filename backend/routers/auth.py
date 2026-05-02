"""Authentication router: register, login, refresh, logout, me."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User, LanguageEnum
from auth import (
    hash_password,
    verify_password,
    needs_rehash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    language: str = "ar"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    language: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    language: str
    subscription_tier: str
    subscription_expires_at: Optional[datetime]
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        language=user.language,
        subscription_tier=user.subscription_tier,
        subscription_expires_at=user.subscription_expires_at,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login,
    )


async def _send_verification_email(email: str, user_id: str):
    """Stub: replace with real email provider (SendGrid, SES, etc.)."""
    import logging
    logging.getLogger(__name__).info(
        f"[EMAIL STUB] Verification email would be sent to {email} for user {user_id}"
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        language=body.language if body.language in ("ar", "en") else "ar",
        broker_accounts=[],
    )
    db.add(user)
    await db.flush()

    background_tasks.add_task(_send_verification_email, user.email, str(user.id))

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_response(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    # Rehash if needed (argon2 params changed)
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(body.password)

    user.last_login = datetime.now(timezone.utc)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_response(user),
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Client-side logout: instruct frontend to discard tokens.
    Server-side token blacklisting can be added via Redis if needed.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return _user_to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.username is not None:
        # Check uniqueness
        result = await db.execute(
            select(User).where(User.username == body.username, User.id != current_user.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
            )
        current_user.username = body.username
    if body.language is not None and body.language in ("ar", "en"):
        current_user.language = body.language

    await db.flush()
    return _user_to_response(current_user)


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Email verification endpoint.
    In production, send a signed token via email and verify here.
    For now, accepts the JWT access token and marks the user as verified.
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_verified = True
    return {"message": "Email verified successfully"}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )
    current_user.hashed_password = hash_password(body.new_password)
    await db.flush()
    return {"message": "Password changed successfully"}
