"""Common FastAPI dependencies (current user, db session, role checks)."""
from __future__ import annotations

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .core.security import decode_token
from .db.base import get_db
from .db.models import User

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def current_user(
    token: Annotated[str | None, Depends(oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="auth_required")
    data = decode_token(token)
    if not data or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    user = (await db.execute(select(User).where(User.id == data["sub"]))).scalar_one_or_none()
    if not user or user.status == "suspended":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_invalid")
    return user


async def current_user_optional(
    token: Annotated[str | None, Depends(oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Like `current_user` but never raises — for public endpoints that may
    personalize the response when a valid token is present."""
    if not token:
        return None
    data = decode_token(token)
    if not data or data.get("type") != "access":
        return None
    user = (await db.execute(select(User).where(User.id == data["sub"]))).scalar_one_or_none()
    if not user or user.status == "suspended":
        return None
    return user


async def admin_required(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_only")
    return user


async def super_admin_required(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="super_admin_only")
    return user
