"""Subscriptions endpoints."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import current_user
from ..db.base import get_db
from ..db.models import Plan, Subscription, User

router = APIRouter()


class PlanOut(BaseModel):
    id: int
    code: str
    name_ar: str
    name_en: str
    monthly_price: float
    currency: str
    features: dict


@router.get("/plans")
async def plans(db: Annotated[AsyncSession, Depends(get_db)]):
    plans = (await db.execute(select(Plan).where(Plan.is_active == True))).scalars().all()  # noqa: E712
    return [
        PlanOut(
            id=p.id, code=p.code, name_ar=p.name_ar, name_en=p.name_en,
            monthly_price=float(p.monthly_price), currency=p.currency,
            features=p.features_json or {},
        ).model_dump()
        for p in plans
    ]


class CreateSubIn(BaseModel):
    plan_code: str
    payment_provider: str  # mada | stripe | paypal | applepay


@router.get("/me")
async def my_subscription(user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    sub = (
        await db.execute(
            select(Subscription).where(Subscription.user_id == user.id, Subscription.status.in_(["active", "trialing"]))
            .order_by(Subscription.created_at.desc())
        )
    ).scalars().first()
    if not sub:
        return {"ok": True, "subscription": None}
    plan = (await db.execute(select(Plan).where(Plan.id == sub.plan_id))).scalar_one()
    return {"ok": True, "subscription": {
        "id": str(sub.id),
        "plan_code": plan.code,
        "status": sub.status,
        "current_end": sub.current_end.isoformat(),
        "auto_renew": sub.auto_renew,
    }}
