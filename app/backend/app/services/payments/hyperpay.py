"""HyperPay (MADA + Visa for Saudi market) — Server-to-Server Checkout.

Docs: https://wordpresshyperpay.docs.oppwa.com/integrations/server-to-server
"""
from __future__ import annotations
import httpx
from ...core.config import settings


class HyperPayClient:
    def __init__(self) -> None:
        self.base = settings.HYPERPAY_BASE_URL
        self.token = settings.HYPERPAY_ACCESS_TOKEN.get_secret_value() if settings.HYPERPAY_ACCESS_TOKEN else ""
        self.entity_mada = settings.HYPERPAY_ENTITY_ID_MADA or ""
        self.entity_visa = settings.HYPERPAY_ENTITY_ID_VISA or ""

    async def create_checkout(self, *, amount: float, currency: str, brand: str = "MADA") -> dict:
        entity = self.entity_mada if brand == "MADA" else self.entity_visa
        if not entity or not self.token:
            return {"error": "hyperpay_not_configured"}
        async with httpx.AsyncClient(timeout=15) as cx:
            r = await cx.post(
                f"{self.base}/v1/checkouts",
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "entityId": entity,
                    "amount": f"{amount:.2f}",
                    "currency": currency,
                    "paymentType": "DB",
                },
            )
            r.raise_for_status()
            data = r.json()
            return {
                "id": data.get("id"),
                "result_code": (data.get("result") or {}).get("code"),
                "redirect_url": f"{settings.APP_URL}/checkout/hyperpay?id={data.get('id')}",
                "raw": data,
            }
