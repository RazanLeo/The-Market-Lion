"""Stripe — Visa/MC/AmEx + Apple Pay.

The `stripe` SDK is optional at import time so the app can run without it
(e.g. local dev / CI smoke tests). Production deploys must pip-install stripe.
"""
from __future__ import annotations
from typing import Any
try:  # optional dependency
    import stripe  # type: ignore
except ImportError:  # pragma: no cover
    stripe = None  # type: ignore
from ...core.config import settings


class StripeClient:
    def __init__(self) -> None:
        if stripe is not None and settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY.get_secret_value()

    async def create_session(self, *, amount_cents: int, currency: str, plan_code: str, user_email: str) -> dict[str, Any]:
        if stripe is None or not getattr(stripe, "api_key", None):
            return {"error": "stripe_not_configured"}
        sess = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=user_email,
            line_items=[{"price_data": {
                "currency": currency,
                "unit_amount": amount_cents,
                "product_data": {"name": f"The Market Lion — {plan_code}"},
                "recurring": {"interval": "month"},
            }, "quantity": 1}],
            success_url=f"{settings.APP_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.APP_URL}/checkout/cancel",
            metadata={"plan_code": plan_code},
        )
        return {"id": sess.id, "redirect_url": sess.url, "plan_code": plan_code}

    async def create_apple_pay_session(self, *, amount_cents: int, currency: str, plan_code: str, user_email: str) -> dict[str, Any]:
        # Apple Pay rides on Stripe Payment Element with payment_method_types=['card','apple_pay']
        return await self.create_session(amount_cents=amount_cents, currency=currency, plan_code=plan_code, user_email=user_email)

    def verify_webhook(self, body: bytes, sig_header: str | None) -> dict | None:
        if stripe is None or not settings.STRIPE_WEBHOOK_SECRET or not sig_header:
            return None
        try:
            return stripe.Webhook.construct_event(body, sig_header, settings.STRIPE_WEBHOOK_SECRET.get_secret_value())
        except Exception:
            return None
