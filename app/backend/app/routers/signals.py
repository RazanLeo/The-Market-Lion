"""Signals — Buy Lion / Sell Lion / Buy Cub / Sell Cub list."""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import current_user
from ..db.base import get_db
from ..db.models import User, ConfluenceScoreRow

router = APIRouter()


@router.get("/recent")
async def recent_signals(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    symbol: str = Query(...),
    tf: str = "15M",
    limit: int = 50,
):
    rows = (await db.execute(
        select(ConfluenceScoreRow).where(ConfluenceScoreRow.symbol == symbol, ConfluenceScoreRow.tf == tf)
        .order_by(desc(ConfluenceScoreRow.ts)).limit(limit)
    )).scalars().all()
    out = []
    for r in rows:
        if r.decision in ("buy", "sell") and float(r.total_pct or 0) >= 60:
            out.append({
                "ts": r.ts.isoformat(),
                "kind": "Buy Lion" if r.decision == "buy" and float(r.total_pct or 0) >= 80 else
                        "Sell Lion" if r.decision == "sell" and float(r.total_pct or 0) >= 80 else
                        "Buy Cub" if r.decision == "buy" else "Sell Cub",
                "decision": r.decision,
                "score": float(r.total_pct or 0),
            })
    return {"ok": True, "items": out}
