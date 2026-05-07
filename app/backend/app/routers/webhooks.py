"""Inbound webhooks for payment providers."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_db
from ..db.models import Payment, Subscription, Plan
from ..services.payments.stripe_client import StripeClient

router = APIRouter()


@router.post("/payments/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    sig = request.headers.get("stripe-signature")
    event = StripeClient().verify_webhook(body, sig)
    if not event:
        raise HTTPException(400, detail="invalid_sig")
    if event["type"] in ("checkout.session.completed", "invoice.paid"):
        ext_id = event["data"]["object"]["id"]
        payment = (await db.execute(select(Payment).where(Payment.provider_ref == ext_id))).scalar_one_or_none()
        if payment:
            payment.status = "succeeded"
            await _activate_subscription(db, payment)
            await db.flush()
    return {"ok": True}


@router.post("/payments/paypal")
async def paypal_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    if body.get("event_type") == "PAYMENT.CAPTURE.COMPLETED":
        ext_id = body["resource"]["id"]
        payment = (await db.execute(select(Payment).where(Payment.provider_ref == ext_id))).scalar_one_or_none()
        if payment:
            payment.status = "succeeded"
            await _activate_subscription(db, payment)
            await db.flush()
    return {"ok": True}


@router.post("/payments/mada")
async def hyperpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    ext_id = body.get("id")
    payment = (await db.execute(select(Payment).where(Payment.provider_ref == ext_id))).scalar_one_or_none()
    if payment and body.get("result", {}).get("code", "").startswith("000.000"):
        payment.status = "succeeded"
        await _activate_subscription(db, payment)
        await db.flush()
    return {"ok": True}


async def _activate_subscription(db: AsyncSession, payment: Payment):
    plan = None
    # Find plan from amount lookup or store plan_id in raw_payload
    if payment.raw_payload and (code := payment.raw_payload.get("plan_code")):
        plan = (await db.execute(select(Plan).where(Plan.code == code))).scalar_one_or_none()
    if not plan:
        plan = (await db.execute(select(Plan).where(Plan.monthly_price == payment.amount))).scalar_one_or_none()
    if not plan:
        return
    now = datetime.now(timezone.utc)
    sub = Subscription(
        user_id=payment.user_id, plan_id=plan.id,
        status="active", current_start=now, current_end=now + timedelta(days=30),
        auto_renew=True, payment_provider=payment.provider, external_id=payment.provider_ref,
    )
    db.add(sub)
    payment.subscription_id = sub.id
