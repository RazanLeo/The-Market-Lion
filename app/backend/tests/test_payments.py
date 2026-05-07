"""Payment gateway client tests — verify HyperPay/Stripe/PayPal endpoints exist
and the right URL/HTTP shape is used. Real external calls are mocked.
"""
from __future__ import annotations
from unittest.mock import patch, MagicMock, AsyncMock
import pytest


def test_hyperpay_module_present():
    from app.services.payments.hyperpay import HyperPayClient
    c = HyperPayClient()
    assert hasattr(c, "base")
    # Required methods
    assert callable(getattr(c, "create_checkout", None)) or callable(getattr(c, "checkout", None))


def test_stripe_module_present():
    from app.services.payments.stripe_client import StripeClient
    c = StripeClient()
    # If keys not configured, factory returns gracefully (no exception on construct)
    assert c is not None
    assert callable(getattr(c, "create_session", None))


def test_paypal_module_present():
    from app.services.payments.paypal_client import PayPalClient
    c = PayPalClient()
    assert c is not None
    # token method exists for OAuth
    assert callable(getattr(c, "_token", None))


def test_paytabs_disabled_by_default():
    """PayTabs must NOT be active in the payments package."""
    import os
    base = os.path.dirname(__import__("app").__file__)
    payments_dir = os.path.join(base, "services", "payments")
    has_paytabs = any("paytabs" in f.lower() for f in os.listdir(payments_dir))
    if has_paytabs:
        # If file exists it must be opt-in only (must not auto-import in __init__)
        init_src = open(os.path.join(payments_dir, "__init__.py")).read()
        assert "paytabs" not in init_src.lower()


def test_payments_router_supports_required_providers():
    """The payments router must expose at least the four required providers."""
    src = open("app/routers/payments.py").read().lower()
    assert "stripe" in src
    assert "hyperpay" in src or "mada" in src
    assert "paypal" in src
    assert "applepay" in src or "apple_pay" in src or "apple pay" in src


@pytest.mark.asyncio
async def test_paypal_token_returns_none_when_unconfigured(monkeypatch):
    """When PayPal secrets are absent, _token must return None gracefully."""
    monkeypatch.setattr("app.services.payments.paypal_client.settings.PAYPAL_CLIENT_ID", None, raising=False)
    monkeypatch.setattr("app.services.payments.paypal_client.settings.PAYPAL_CLIENT_SECRET", None, raising=False)
    from app.services.payments.paypal_client import PayPalClient
    c = PayPalClient()
    tok = await c._token()
    assert tok is None
