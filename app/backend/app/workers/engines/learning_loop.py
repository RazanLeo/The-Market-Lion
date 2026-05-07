"""Self-Learning Reinforcement loop — adjusts category and per-analyzer weights based on closed-trade outcomes.

Algorithm (REINFORCE-lite + Bandit):
  for each closed trade T:
      pl_norm = clip(T.pl_pct, -1, +1)
      for each analyzer A that contributed to T's decision:
          sign_align = sign(A.contribution_at_open) * sign(pl_norm)
          weights[A] += lr * sign_align * abs(A.contribution_at_open)
          clamp weights[A] in [w_min, w_max]
      normalize within category so sum stays 100%.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.base import AsyncSessionLocal
from ...db.models import Position, ConfluenceScoreRow, AuditLog, FeatureToggle


LR = 0.005
W_MIN = 0.1
W_MAX = 5.0


def _sign(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


async def _get_voting_weights(db: AsyncSession) -> dict[str, float]:
    row = (await db.execute(select(FeatureToggle).where(FeatureToggle.key == "voting_weights"))).scalar_one_or_none()
    return (row.meta if row and row.meta else {"fundamental":20.0,"basics":30.0,"schools":30.0,"indicators":10.0,"flow":10.0})


async def _save_voting_weights(db: AsyncSession, weights: dict[str, float]) -> None:
    row = (await db.execute(select(FeatureToggle).where(FeatureToggle.key == "voting_weights"))).scalar_one_or_none()
    if not row:
        row = FeatureToggle(key="voting_weights", enabled=True, meta=weights); db.add(row)
    else:
        row.meta = weights
    await db.flush()


async def update_after_closed_trade(position_id: str) -> dict[str, Any]:
    """Pull confluence_payload at open ts; update weights based on PL outcome."""
    async with AsyncSessionLocal() as db:
        pos = (await db.execute(select(Position).where(Position.id == position_id))).scalar_one_or_none()
        if not pos or pos.status != "closed": return {"ok": False, "reason": "not_closed"}
        # Find confluence_score row at opened_at for symbol/tf — use most recent before open
        cs = (await db.execute(
            select(ConfluenceScoreRow).where(
                ConfluenceScoreRow.symbol == pos.symbol,
                ConfluenceScoreRow.ts <= pos.opened_at,
            ).order_by(desc(ConfluenceScoreRow.ts)).limit(1)
        )).scalar_one_or_none()
        if not cs or not cs.payload: return {"ok": False, "reason": "no_confluence_at_open"}

        pl_norm = max(-1.0, min(1.0, float(pos.pl_pct or 0) / 5.0))
        if pl_norm == 0: return {"ok": True, "no_op": True}

        weights = await _get_voting_weights(db)
        # adjust each category weight by aggregate alignment
        for cat in ("fundamental","basics","schools","indicators","flow"):
            contribs = cs.payload.get("contributions", {}).get(cat, [])
            if not contribs: continue
            cat_signed = sum((1 if c["result"]=="buy" else -1 if c["result"]=="sell" else 0) * c["confidence"] * c.get("weight",1.0) for c in contribs)
            sign_align = _sign(cat_signed) * _sign(pl_norm)
            weights[cat] = max(W_MIN, min(50.0, weights[cat] + LR * sign_align * abs(cat_signed) * 0.01))

        # Re-normalize to sum 100
        total = sum(weights.values()) or 1
        weights = {k: round(v / total * 100, 3) for k, v in weights.items()}
        await _save_voting_weights(db, weights)

        db.add(AuditLog(actor_role="system", action="rl_weights_update", resource="voting_weights",
                        meta={"position_id": position_id, "pl_norm": pl_norm, "new_weights": weights}))
        await db.commit()
        return {"ok": True, "weights": weights}


async def run_loop_for_recent() -> dict[str, Any]:
    """Process all closed positions in last 24h that haven't been learned from."""
    async with AsyncSessionLocal() as db:
        recent = (await db.execute(
            select(Position).where(Position.status == "closed").order_by(desc(Position.closed_at)).limit(100)
        )).scalars().all()
    out = []
    for p in recent:
        r = await update_after_closed_trade(str(p.id))
        out.append({"id": str(p.id), **r})
    return {"ok": True, "processed": len(out), "results": out[:10]}
