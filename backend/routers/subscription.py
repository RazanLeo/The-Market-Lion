"""Subscription & pricing router."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models.user import User

router = APIRouter()

PLANS = {
    "free": {
        "name_ar": "مجاني", "name_en": "Free",
        "price_sar": 0, "price_usd": 0,
        "features": ["manual_signals", "basic_charts", "1_symbol"],
        "features_ar": ["إشارات يدوية", "شارت TradingView", "أصل واحد فقط"],
        "max_symbols": 1, "auto_trading": False,
    },
    "pro": {
        "name_ar": "برو", "name_en": "Pro",
        "price_sar": 2000, "price_usd": 533,
        "features": ["auto_trading", "all_tables", "telegram", "broker_connect", "10_symbols"],
        "features_ar": ["تداول آلي كامل", "جميع الجداول الأربعة", "إشعارات Telegram", "ربط البروكر", "10 أصول"],
        "max_symbols": 10, "auto_trading": True,
    },
    "vip": {
        "name_ar": "VIP", "name_en": "VIP",
        "price_sar": 6000, "price_usd": 1600,
        "features": ["all_pro", "whale_tracker", "custom_reports", "whatsapp_vip", "api_access"],
        "features_ar": ["كل مميزات برو", "رصد الحيتان الكامل", "تقارير مخصصة", "دعم واتساب VIP", "وصول API"],
        "max_symbols": 999, "auto_trading": True,
    },
}


class SubscribeRequest(BaseModel):
    plan: str
    payment_method: str = "manual"


@router.get("/plans")
async def get_plans():
    return PLANS


@router.get("/my-subscription")
async def get_my_subscription(current_user: User = Depends(get_current_user)):
    plan = PLANS.get(current_user.subscription_tier, PLANS["free"])
    return {
        "tier": current_user.subscription_tier,
        "plan": plan,
        "expires_at": current_user.subscription_expires_at.isoformat() if current_user.subscription_expires_at else None,
        "is_active": True,
    }


@router.post("/subscribe")
async def subscribe(
    req: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.plan not in PLANS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="باقة غير موجودة")

    # In production: integrate with HyperPay/Stripe
    # For now: update user subscription directly
    current_user.subscription_tier = req.plan
    current_user.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    await db.commit()
    return {
        "success": True,
        "message": f"تم الاشتراك في باقة {PLANS[req.plan]['name_ar']} بنجاح",
        "tier": req.plan,
        "expires_at": current_user.subscription_expires_at.isoformat(),
        "payment_url": None,
    }
