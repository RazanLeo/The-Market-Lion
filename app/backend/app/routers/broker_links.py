"""Broker linking — Capital.com primary, Exness disabled at launch."""
from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import encrypt_secret
from ..deps import current_user
from ..db.base import get_db
from ..db.models import BrokerAccount, User
from ..services.brokers.capital import CapitalAdapter

router = APIRouter()


class LinkIn(BaseModel):
    broker: str  # 'capital' | 'exness'
    account_login: str
    api_key: str
    api_password: str
    account_type: str = "demo"  # demo | live


class LinkOut(BaseModel):
    ok: bool = True
    id: str
    broker: str
    account_type: str
    base_currency: str | None
    leverage_max: int | None


@router.get("")
async def list_links(user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.execute(select(BrokerAccount).where(BrokerAccount.user_id == user.id, BrokerAccount.is_active == True))).scalars().all()  # noqa: E712
    return [
        {"id": str(r.id), "broker": r.broker, "account_login": r.account_login, "account_type": r.account_type, "base_currency": r.base_currency, "leverage_max": r.leverage_max}
        for r in rows
    ]


@router.post("", response_model=LinkOut)
async def add_link(
    body: LinkIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.broker == "exness" and not settings.EXNESS_ENABLED:
        raise HTTPException(409, detail="exness_disabled_at_launch")
    if body.broker not in ("capital", "exness"):
        raise HTTPException(400, detail="unknown_broker")

    # Validate by fetching balance
    if body.broker == "capital":
        client = CapitalAdapter(demo=body.account_type == "demo")
        try:
            await client.create_session(api_key=body.api_key, identifier=body.account_login, password=body.api_password)
            acct_info = await client.account_info()
        except Exception as e:
            raise HTTPException(400, detail=f"capital_auth_failed: {e}")
        base_currency = acct_info.get("currency")
        leverage_max = None
    else:
        base_currency = None
        leverage_max = None

    row = BrokerAccount(
        user_id=user.id,
        broker=body.broker,
        account_login=body.account_login,
        api_key_enc=encrypt_secret(body.api_key),
        api_secret_enc=encrypt_secret(body.api_password),
        account_type=body.account_type,
        base_currency=base_currency,
        leverage_max=leverage_max,
    )
    db.add(row)
    await db.flush()
    return LinkOut(id=str(row.id), broker=row.broker, account_type=row.account_type, base_currency=base_currency, leverage_max=leverage_max)


@router.delete("/{link_id}")
async def remove_link(link_id: str, user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    row = (await db.execute(select(BrokerAccount).where(BrokerAccount.id == link_id, BrokerAccount.user_id == user.id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404)
    row.is_active = False
    await db.flush()
    return {"ok": True}


@router.get("/{link_id}/balance")
async def balance(link_id: str, user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    row = (await db.execute(select(BrokerAccount).where(BrokerAccount.id == link_id, BrokerAccount.user_id == user.id, BrokerAccount.is_active == True))).scalar_one_or_none()  # noqa: E712
    if not row:
        raise HTTPException(404)
    if row.broker != "capital":
        raise HTTPException(409, detail="broker_not_supported")
    from ..core.security import decrypt_secret
    client = CapitalAdapter(demo=row.account_type == "demo")
    await client.create_session(
        api_key=decrypt_secret(row.api_key_enc),
        identifier=row.account_login,
        password=decrypt_secret(row.api_secret_enc),
    )
    return await client.account_info()
