"""Trading positions — manual/auto open + close + modify; reads via Capital.com."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import current_user
from ..db.base import get_db
from ..db.models import User, BrokerAccount, Position, TradePlan, TradeEvent
from ..core.security import decrypt_secret
from ..services.brokers.capital import CapitalAdapter
from ..workers.engines.risk_engine import build_trade_plan

router = APIRouter()


class ManualOpenIn(BaseModel):
    broker_account_id: str
    symbol: str
    side: str  # 'buy' | 'sell'
    risk_pct: float = 1.0
    tf: str = "15M"
    confidence: float | None = None


@router.post("/manual")
async def manual_open(
    body: ManualOpenIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    acct = (await db.execute(
        select(BrokerAccount).where(BrokerAccount.id == body.broker_account_id, BrokerAccount.user_id == user.id, BrokerAccount.is_active == True)  # noqa: E712
    )).scalar_one_or_none()
    if not acct:
        raise HTTPException(404, detail="broker_account_not_found")
    client = CapitalAdapter(demo=acct.account_type == "demo")
    await client.create_session(api_key=decrypt_secret(acct.api_key_enc), identifier=acct.account_login, password=decrypt_secret(acct.api_secret_enc))

    info = await client.account_info()
    balance = float(info.get("balance", 0))
    plan_dict = await build_trade_plan(symbol=body.symbol, side=body.side, balance=balance, risk_pct=body.risk_pct, tf=body.tf, broker=client)

    plan_row = TradePlan(
        user_id=user.id, symbol=body.symbol, side=body.side, tf=body.tf,
        entry_price=Decimal(str(plan_dict["entry"])),
        tp1_price=Decimal(str(plan_dict["tp1"])), tp2_price=Decimal(str(plan_dict["tp2"])),
        tp3_price=Decimal(str(plan_dict["tp3"])), final_tp_price=Decimal(str(plan_dict["final_tp"])),
        sl_price=Decimal(str(plan_dict["sl"])),
        lot_size=Decimal(str(plan_dict["lot"])), leverage=plan_dict["leverage"],
        risk_pct=Decimal(str(body.risk_pct)), risk_amount=Decimal(str(plan_dict["risk_amount"])),
        confidence=Decimal(str(body.confidence or 0)), status="executed",
    )
    db.add(plan_row)
    await db.flush()

    deal = await client.open_market(symbol=body.symbol, side=body.side, lot=plan_dict["lot"], sl=plan_dict["sl"], tp=plan_dict["tp1"])
    pos = Position(
        user_id=user.id, broker_account_id=acct.id, trade_plan_id=plan_row.id,
        broker_ticket=deal.get("dealId") or deal.get("dealReference"),
        symbol=body.symbol, side=body.side, lot_size=Decimal(str(plan_dict["lot"])),
        entry_price=Decimal(str(plan_dict["entry"])), tp_price=Decimal(str(plan_dict["tp1"])),
        sl_price=Decimal(str(plan_dict["sl"])), trailing_sl=Decimal(str(plan_dict["sl"])),
        status="open",
    )
    db.add(pos)
    await db.flush()
    db.add(TradeEvent(position_id=pos.id, event="open", meta={"deal": deal, "plan": plan_dict}))
    await db.flush()
    return {"ok": True, "position_id": str(pos.id), "deal": deal, "plan": plan_dict}


@router.get("/open")
async def open_positions(user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.execute(select(Position).where(Position.user_id == user.id, Position.status == "open").order_by(desc(Position.opened_at)))).scalars().all()
    return [{
        "id": str(r.id), "symbol": r.symbol, "side": r.side, "lot": float(r.lot_size or 0),
        "entry": float(r.entry_price or 0), "sl": float(r.sl_price or 0), "tp": float(r.tp_price or 0),
        "pl": float(r.pl), "pl_pct": float(r.pl_pct), "opened_at": r.opened_at.isoformat(),
    } for r in rows]


@router.get("/history")
async def history(user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)], limit: int = 100):
    rows = (await db.execute(select(Position).where(Position.user_id == user.id).order_by(desc(Position.opened_at)).limit(limit))).scalars().all()
    return [{
        "id": str(r.id), "symbol": r.symbol, "side": r.side, "status": r.status,
        "lot": float(r.lot_size or 0), "entry": float(r.entry_price or 0), "exit": float(r.exit_price or 0),
        "pl": float(r.pl), "pl_pct": float(r.pl_pct),
        "opened_at": r.opened_at.isoformat(), "closed_at": r.closed_at.isoformat() if r.closed_at else None,
    } for r in rows]


@router.post("/{position_id}/close")
async def close_position(
    position_id: str,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    pos = (await db.execute(select(Position).where(Position.id == position_id, Position.user_id == user.id, Position.status == "open"))).scalar_one_or_none()
    if not pos:
        raise HTTPException(404)
    acct = (await db.execute(select(BrokerAccount).where(BrokerAccount.id == pos.broker_account_id))).scalar_one()
    client = CapitalAdapter(demo=acct.account_type == "demo")
    await client.create_session(api_key=decrypt_secret(acct.api_key_enc), identifier=acct.account_login, password=decrypt_secret(acct.api_secret_enc))
    await client.close_position(deal_id=pos.broker_ticket or "")
    pos.status = "closed"
    pos.closed_at = datetime.now(timezone.utc)
    await db.flush()
    db.add(TradeEvent(position_id=pos.id, event="manual_close"))
    await db.flush()
    return {"ok": True}


class AutoToggleIn(BaseModel):
    broker_account_id: str
    enable: bool


@router.post("/auto/toggle")
async def auto_toggle(
    body: AutoToggleIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from ..db.models import TradingPreference
    pref = (await db.execute(select(TradingPreference).where(TradingPreference.user_id == user.id))).scalar_one_or_none()
    if not pref:
        pref = TradingPreference(user_id=user.id)
        db.add(pref)
    pref.bot_enabled = body.enable
    pref.trade_mode = "auto" if body.enable else "manual"
    await db.flush()
    return {"ok": True, "bot_enabled": pref.bot_enabled}
