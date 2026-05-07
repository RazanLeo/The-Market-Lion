"""PayPal Orders v2."""
from __future__ import annotations
import httpx
from ...core.config import settings


class PayPalClient:
    def __init__(self) -> None:
        self.base = settings.PAYPAL_BASE_URL
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.secret = settings.PAYPAL_CLIENT_SECRET.get_secret_value() if settings.PAYPAL_CLIENT_SECRET else None

    async def _token(self) -> str | None:
        if not self.client_id or not self.secret:
            return None
        async with httpx.AsyncClient(timeout=10) as cx:
            r = await cx.post(f"{self.base}/v1/oauth2/token",
                              data={"grant_type": "client_credentials"},
                              auth=(self.client_id, self.secret))
            r.raise_for_status()
            return r.json().get("access_token")

    async def create_order(self, *, amount: float, currency: str, plan_code: str) -> dict:
        token = await self._token()
        if not token:
            return {"error": "paypal_not_configured"}
        async with httpx.AsyncClient(timeout=15) as cx:
            r = await cx.post(f"{self.base}/v2/checkout/orders",
                              headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                              json={
                                  "intent": "CAPTURE",
                                  "purchase_units": [{"amount": {"currency_code": currency, "value": f"{amount:.2f}"}, "custom_id": plan_code}],
                                  "application_context": {
                                      "return_url": f"{settings.APP_URL}/checkout/success",
                                      "cancel_url": f"{settings.APP_URL}/checkout/cancel",
                                  },
                              })
            r.raise_for_status()
            data = r.json()
            approve = next((l["href"] for l in (data.get("links") or []) if l.get("rel") == "approve"), None)
            return {"id": data.get("id"), "redirect_url": approve, "plan_code": plan_code, "raw": data}
