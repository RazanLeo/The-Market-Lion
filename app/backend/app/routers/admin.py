"""Admin Console endpoints (RBAC enforced)."""
from __future__ import annotations
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import admin_required, super_admin_required
from ..db.base import get_db
from ..db.models import User, Subscription, Payment, AuditLog, FeatureToggle, Plan

router = APIRouter()


@router.get("/dashboard")
async def dashboard(_: Annotated[User, Depends(admin_required)], db: Annotated[AsyncSession, Depends(get_db)]):
    n_users = (await db.execute(select(func.count(User.id)))).scalar()
    n_active_subs = (await db.execute(select(func.count(Subscription.id)).where(Subscription.status == "active"))).scalar()
    n_paid = (await db.execute(select(func.count(Payment.id)).where(Payment.status == "succeeded"))).scalar()
    return {"ok": True, "users": n_users, "active_subscriptions": n_active_subs, "successful_payments": n_paid}


@router.get("/users")
async def list_users(_: Annotated[User, Depends(admin_required)], db: Annotated[AsyncSession, Depends(get_db)], q: str | None = None, limit: int = 100):
    stmt = select(User).order_by(desc(User.created_at)).limit(limit)
    if q:
        stmt = select(User).where(User.email.ilike(f"%{q}%")).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [{"id": str(r.id), "email": r.email, "role": r.role, "status": r.status, "lang": r.preferred_lang, "created": r.created_at.isoformat()} for r in rows]


class UserActionIn(BaseModel):
    action: str  # suspend | activate | reset_password | force_2fa


@router.post("/users/{user_id}/action")
async def user_action(user_id: str, body: UserActionIn, admin: Annotated[User, Depends(admin_required)], db: Annotated[AsyncSession, Depends(get_db)]):
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not target:
        raise HTTPException(404)
    if body.action == "suspend":
        target.status = "suspended"
    elif body.action == "activate":
        target.status = "active"
    else:
        raise HTTPException(400, detail="unknown_action")
    db.add(AuditLog(actor_id=admin.id, actor_role=admin.role, action=f"user_{body.action}", resource="user", resource_id=user_id))
    await db.flush()
    return {"ok": True}


@router.get("/payments")
async def list_payments(_: Annotated[User, Depends(admin_required)], db: Annotated[AsyncSession, Depends(get_db)], limit: int = 100):
    rows = (await db.execute(select(Payment).order_by(desc(Payment.created_at)).limit(limit))).scalars().all()
    return [{"id": str(r.id), "user_id": str(r.user_id), "provider": r.provider, "amount": float(r.amount), "currency": r.currency, "status": r.status, "ts": r.created_at.isoformat()} for r in rows]


@router.get("/audit")
async def audit(_: Annotated[User, Depends(admin_required)], db: Annotated[AsyncSession, Depends(get_db)], limit: int = 200):
    rows = (await db.execute(select(AuditLog).order_by(desc(AuditLog.ts)).limit(limit))).scalars().all()
    return [{"id": r.id, "ts": r.ts.isoformat(), "actor_role": r.actor_role, "action": r.action, "resource": r.resource, "resource_id": r.resource_id} for r in rows]


@router.get("/feature-toggles")
async def list_toggles(_: Annotated[User, Depends(admin_required)], db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.execute(select(FeatureToggle))).scalars().all()
    return [{"key": r.key, "enabled": r.enabled, "meta": r.meta or {}} for r in rows]


class ToggleIn(BaseModel):
    key: str
    enabled: bool


@router.post("/feature-toggles")
async def set_toggle(body: ToggleIn, admin: Annotated[User, Depends(super_admin_required)], db: Annotated[AsyncSession, Depends(get_db)]):
    row = (await db.execute(select(FeatureToggle).where(FeatureToggle.key == body.key))).scalar_one_or_none()
    if not row:
        row = FeatureToggle(key=body.key, enabled=body.enabled)
        db.add(row)
    else:
        row.enabled = body.enabled
    db.add(AuditLog(actor_id=admin.id, actor_role=admin.role, action="toggle_set", resource="feature_toggle", resource_id=body.key, meta={"enabled": body.enabled}))
    await db.flush()
    return {"ok": True}


class VotingWeightsIn(BaseModel):
    weights: dict[str, float]  # {category: weight}; must sum to 100


@router.post("/voting-weights")
async def set_voting_weights(body: VotingWeightsIn, admin: Annotated[User, Depends(super_admin_required)], db: Annotated[AsyncSession, Depends(get_db)]):
    if abs(sum(body.weights.values()) - 100) > 0.01:
        raise HTTPException(400, detail="weights_must_sum_100")
    row = (await db.execute(select(FeatureToggle).where(FeatureToggle.key == "voting_weights"))).scalar_one_or_none()
    if not row:
        row = FeatureToggle(key="voting_weights", enabled=True, meta=body.weights)
        db.add(row)
    else:
        row.meta = body.weights
    db.add(AuditLog(actor_id=admin.id, actor_role=admin.role, action="voting_weights_set", resource="config", meta=body.weights))
    await db.flush()
    return {"ok": True}
