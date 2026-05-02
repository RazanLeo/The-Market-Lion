"""Admin dashboard router: user management, platform statistics."""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from auth import get_current_user
from database import get_db
from models.user import User
from models.trade import Trade
from models.subscription import Subscription

router = APIRouter()


# ── Admin guard ───────────────────────────────────────────────────────────────

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Schemas ───────────────────────────────────────────────────────────────────

class UpdateSubscriptionRequest(BaseModel):
    tier: str
    expires_at: Optional[datetime] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    tier: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List all users with pagination and optional filtering."""
    query = select(User)

    if search:
        query = query.where(
            (User.email.ilike(f"%{search}%"))
            | (User.full_name.ilike(f"%{search}%"))
            | (User.username.ilike(f"%{search}%"))
        )
    if tier:
        query = query.where(User.subscription_tier == tier)

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginated results
    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(User.created_at.desc())
    )
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "full_name": u.full_name,
                "language": u.language,
                "subscription_tier": u.subscription_tier,
                "subscription_expires_at": u.subscription_expires_at.isoformat()
                if u.subscription_expires_at
                else None,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.put("/user/{user_id}/subscription")
async def update_user_subscription(
    user_id: str,
    body: UpdateSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Manually change a user's subscription tier."""
    valid_tiers = ("free", "pro", "vip", "enterprise")
    if body.tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {body.tier}. Must be one of {valid_tiers}",
        )

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.subscription_tier = body.tier
    if body.expires_at:
        user.subscription_expires_at = body.expires_at
    await db.flush()

    return {
        "status": "updated",
        "user_id": user_id,
        "new_tier": body.tier,
        "expires_at": user.subscription_expires_at.isoformat()
        if user.subscription_expires_at
        else None,
    }


@router.put("/user/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Activate or deactivate a user account."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    await db.flush()
    return {"user_id": user_id, "is_active": user.is_active}


@router.get("/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Platform-wide statistics for admin dashboard."""
    now = datetime.now(timezone.utc)
    month_ago = now - timedelta(days=30)

    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    active_users = (
        await db.execute(select(func.count(User.id)).where(User.is_active == True))  # noqa: E712
    ).scalar_one()
    new_users_this_month = (
        await db.execute(
            select(func.count(User.id)).where(User.created_at >= month_ago)
        )
    ).scalar_one()

    tiers: dict = {}
    for tier in ("free", "pro", "vip", "enterprise"):
        count = (
            await db.execute(
                select(func.count(User.id)).where(User.subscription_tier == tier)
            )
        ).scalar_one()
        tiers[tier] = count

    total_trades = (await db.execute(select(func.count(Trade.id)))).scalar_one()
    open_trades = (
        await db.execute(select(func.count(Trade.id)).where(Trade.status == "open"))
    ).scalar_one()

    PLAN_PRICES = {
        "pro": {"price_sar": 2000, "price_usd": 533},
        "vip": {"price_sar": 6000, "price_usd": 1600},
        "enterprise": {"price_sar": 0, "price_usd": 0},
    }
    revenue_sar = sum(
        tiers.get(tier, 0) * info["price_sar"]
        for tier, info in PLAN_PRICES.items()
    )
    revenue_usd = sum(
        tiers.get(tier, 0) * info["price_usd"]
        for tier, info in PLAN_PRICES.items()
    )

    from routers.bot import _bot_state
    active_bots = sum(1 for v in _bot_state.values() if v.get("running"))

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_this_month": new_users_this_month,
            "by_tier": tiers,
        },
        "trades": {
            "total": total_trades,
            "open": open_trades,
        },
        "revenue": {
            "monthly_sar": revenue_sar,
            "monthly_usd": revenue_usd,
        },
        "bots": {
            "active": active_bots,
        },
        "generated_at": now.isoformat(),
    }


@router.get("/trades")
async def get_all_trades(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    symbol: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get all trades across all users (admin view)."""
    query = select(Trade)

    if symbol:
        query = query.where(Trade.symbol == symbol.upper())
    if status_filter:
        query = query.where(Trade.status == status_filter)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(Trade.created_at.desc())
    )
    result = await db.execute(query)
    trades = result.scalars().all()

    return {
        "trades": [
            {
                "id": str(t.id),
                "user_id": str(t.user_id),
                "symbol": t.symbol,
                "broker": t.broker,
                "side": t.side,
                "entry_price": t.entry_price,
                "stop_loss": t.stop_loss,
                "take_profit_1": t.take_profit_1,
                "lot_size": t.lot_size,
                "status": t.status,
                "pnl": t.pnl,
                "confluence_score": t.confluence_score,
                "signal_source": t.signal_source,
                "open_time": t.open_time.isoformat() if t.open_time else None,
                "close_time": t.close_time.isoformat() if t.close_time else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in trades
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }
