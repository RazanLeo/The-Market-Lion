"""User profile + preferences."""
from __future__ import annotations
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import current_user
from ..db.base import get_db
from ..db.models import User, TradingPreference

router = APIRouter()


class MeOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    status: str
    preferred_lang: str
    preferred_tz: str
    twofa_enabled: bool


@router.get("/me", response_model=MeOut)
async def me(user: Annotated[User, Depends(current_user)]):
    return MeOut(
        id=str(user.id), email=user.email, full_name=user.full_name,
        role=user.role, status=user.status, preferred_lang=user.preferred_lang,
        preferred_tz=user.preferred_tz, twofa_enabled=user.twofa_enabled,
    )


class PrefIn(BaseModel):
    default_symbol: str | None = None
    risk_pct: float | None = None
    default_tf: str | None = None
    reference_tf: str | None = None
    trade_mode: str | None = None
    bot_enabled: bool | None = None
    custom_palette: dict[str, Any] | None = None
    toggles_json: dict[str, Any] | None = None
    preferred_lang: str | None = None
    preferred_tz: str | None = None


@router.put("/me/preferences")
async def update_prefs(
    body: PrefIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    pref = (await db.execute(select(TradingPreference).where(TradingPreference.user_id == user.id))).scalar_one_or_none()
    if not pref:
        pref = TradingPreference(user_id=user.id)
        db.add(pref)
    fields = body.model_dump(exclude_none=True)
    if "preferred_lang" in fields:
        user.preferred_lang = fields.pop("preferred_lang")
    if "preferred_tz" in fields:
        user.preferred_tz = fields.pop("preferred_tz")
    for k, v in fields.items():
        setattr(pref, k, v)
    await db.flush()
    return {"ok": True}
