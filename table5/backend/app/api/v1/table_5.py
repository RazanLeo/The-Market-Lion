# ═══════════════════════════════════════════════════════════════════════════
# 🦁 API الجدول الخامس — REST + WebSocket
# ═══════════════════════════════════════════════════════════════════════════
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.core.constants import (
    TIMEFRAMES, TIMEFRAME_WEIGHTS, TIER_VALUES, TOTAL_TIER_SUM,
    SIGNAL_THRESHOLDS, DECISION_THRESHOLD,
)
from app.indicators.registry import get_all_71_indicators, count_by_tier, count_by_category
from app.voting.engine import Table5VotingEngine, Table5Decision
from app.services.market_data import fetch_ohlcv_per_tf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/table-5", tags=["table-5"])
_engine = Table5VotingEngine()


# ─── REST ──────────────────────────────────────────────────────────────────
@router.get("/meta")
async def get_meta():
    """معلومات الجدول الخامس: الأوزان، التوزيع، العتبات"""
    return {
        "module_weight_pct": 10.0,
        "indicators_count": 71,
        "timeframes": TIMEFRAMES,
        "timeframe_weights": TIMEFRAME_WEIGHTS,
        "tier_values": TIER_VALUES,
        "total_tier_sum": TOTAL_TIER_SUM,
        "signal_thresholds": SIGNAL_THRESHOLDS,
        "decision_threshold": DECISION_THRESHOLD,
        "tier_distribution": count_by_tier(),
        "category_distribution": count_by_category(),
    }


@router.get("/indicators")
async def list_indicators():
    """قائمة الـ 71 مؤشر مع التفاصيل"""
    inds = get_all_71_indicators()
    return [
        {
            "id": ind.id,
            "name": ind.name,
            "category": ind.category,
            "category_en": ind.category_en,
            "tier": ind.tier,
            "weight": ind.weight,
            "weight_pct": ind.weight * 100,
            "min_bars": ind.min_bars,
        }
        for ind in inds
    ]


@router.get("/decision")
async def get_decision(
    symbol: str = Query(..., description="رمز الأصل، مثل XAU/USD"),
    include_indicators: bool = Query(True, description="هل نُرجع تفاصيل كل مؤشر؟"),
):
    """احسب القرار اللحظي للجدول الخامس على رمز"""
    try:
        ohlcv_per_tf = await fetch_ohlcv_per_tf(symbol)
    except Exception as e:
        logger.exception("فشل جلب OHLCV")
        raise HTTPException(status_code=502, detail=f"فشل جلب بيانات السوق: {e}")

    decision: Table5Decision = _engine.evaluate(
        symbol=symbol,
        timestamp=datetime.now(timezone.utc).isoformat(),
        ohlcv_per_tf=ohlcv_per_tf,
    )

    payload = {
        "symbol": decision.symbol,
        "timestamp": decision.timestamp,
        "net_score": decision.net_score,
        "confidence": decision.confidence,
        "decision": decision.decision,
        "signal_level": decision.signal_level,
        "filters": {
            "choppiness_applied": decision.choppiness_applied,
            "htf_veto_applied": decision.htf_veto_applied,
            "convergence_boost": decision.convergence_boost,
            "tier_s_consensus": decision.tier_s_consensus,
        },
    }
    if include_indicators:
        payload["indicators"] = [
            {
                "indicator_id": r.indicator_id,
                "indicator_name": r.indicator_name,
                "category": r.category,
                "tier": r.tier,
                "weight": r.weight,
                "signals": r.signals,
                "weighted_score": r.weighted_score,
                "confidence": r.confidence,
                "direction": r.direction,
                "raw_values": r.raw_values,
            }
            for r in decision.indicators
        ]
    return payload


# ─── WebSocket — تحديث لحظي ─────────────────────────────────────────────────
@router.websocket("/ws/{symbol}")
async def websocket_table5(websocket: WebSocket, symbol: str):
    """تدفق لحظي للقرار كل 5 ثوانٍ"""
    await websocket.accept()
    try:
        while True:
            try:
                ohlcv_per_tf = await fetch_ohlcv_per_tf(symbol)
                decision = _engine.evaluate(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    ohlcv_per_tf=ohlcv_per_tf,
                )
                payload = {
                    "type": "table5_update",
                    "symbol": decision.symbol,
                    "timestamp": decision.timestamp,
                    "net_score": decision.net_score,
                    "confidence": decision.confidence,
                    "decision": decision.decision,
                    "signal_level": decision.signal_level,
                    "indicators": [
                        {
                            "indicator_id": r.indicator_id,
                            "indicator_name": r.indicator_name,
                            "category": r.category,
                            "tier": r.tier,
                            "signals": r.signals,
                            "weighted_score": r.weighted_score,
                            "direction": r.direction,
                        }
                        for r in decision.indicators
                    ],
                }
                await websocket.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception as e:
                logger.exception("خطأ في WebSocket loop")
                await websocket.send_text(json.dumps({"type": "error", "error": str(e)}))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info(f"WebSocket مغلق لـ {symbol}")
