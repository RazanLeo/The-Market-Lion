"""Payments — checkout sessions for HyperPay (MADA/Visa), Stripe, PayPal, Apple Pay; PayTabs disabled by default."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import current_user
from ..db.base import get_db
from ..db.models import Plan, Payment, Subscription, User
from ..services.payments.hyperpay import HyperPayClient
from ..services.payments.stripe_client import StripeClient
from ..services.payments.paypal_client import PayPalClient

router = APIRouter()


class CheckoutIn(BaseModel):
    plan_code: str
    provider: str  # mada | visa_hyperpay | stripe | paypal | applepay


class CheckoutOut(BaseModel):
    ok: bool = True
    provider: str
    checkout_id: str
    redirect_url: str | None = None
    payment_id: str


@router.post("/checkout", response_model=CheckoutOut)
async def create_checkout(
    body: CheckoutIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    plan = (await db.execute(select(Plan).where(Plan.code == body.plan_code, Plan.is_active == True))).scalar_one_or_none()  # noqa: E712
    if not plan:
        raise HTTPException(404, detail="plan_not_found")

    if body.provider == "paytabs":
        raise HTTPException(409, detail="paytabs_disabled")

    if body.provider in ("mada", "visa_hyperpay"):
        client = HyperPayClient()
        result = await client.create_checkout(amount=float(plan.monthly_price), currency=plan.currency, brand="MADA" if body.provider == "mada" else "VISA")
        ext_id = result.get("id")
    elif body.provider == "stripe":
        client = StripeClient()
        result = await client.create_session(amount_cents=int(float(plan.monthly_price) * 100), currency=plan.currency.lower(), plan_code=plan.code, user_email=user.email)
        ext_id = result.get("id")
    elif body.provider == "paypal":
        client = PayPalClient()
        result = await client.create_order(amount=float(plan.monthly_price), currency="USD", plan_code=plan.code)
        ext_id = result.get("id")
    elif body.provider == "applepay":
        client = StripeClient()
        result = await client.create_apple_pay_session(amount_cents=int(float(plan.monthly_price) * 100), currency=plan.currency.lower(), plan_code=plan.code, user_email=user.email)
        ext_id = result.get("id")
    else:
        raise HTTPException(400, detail="unknown_provider")

    payment = Payment(
        user_id=user.id, provider=body.provider, provider_ref=ext_id,
        amount=plan.monthly_price, currency=plan.currency, status="pending",
        raw_payload=result,
    )
    db.add(payment)
    await db.flush()
    return CheckoutOut(provider=body.provider, checkout_id=ext_id or "", redirect_url=result.get("redirect_url"), payment_id=str(payment.id))


@router.get("/history")
async def history(user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.execute(select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc()))).scalars().all()
    return [
        {"id": str(r.id), "provider": r.provider, "amount": float(r.amount), "currency": r.currency, "status": r.status, "ts": r.created_at.isoformat()}
        for r in rows
    ]
