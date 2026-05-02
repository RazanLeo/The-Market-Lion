"""Technical analysis router."""
import asyncio
import logging
from fastapi import APIRouter, Query

from routers.market_data import get_candles, SUPPORTED_SYMBOLS
from services.technical_analysis import ta_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/technical", tags=["Technical Analysis"])


@router.get("/analysis/{symbol:path}")
async def get_technical_analysis(
    symbol: str,
    timeframe: str = Query(default="H1", description="Timeframe: M1, M5, M15, M30, H1, H4, D1, W1"),
    count: int = Query(default=200, ge=20, le=500),
):
    """
    Full multi-school technical analysis for a symbol.
    Returns indicators, school-based signals, confluence score, trade levels.
    """
    symbol = symbol.upper().replace("%2F", "/")
    if symbol not in SUPPORTED_SYMBOLS:
        return {"error": f"Symbol {symbol} not supported", "supported": SUPPORTED_SYMBOLS}

    # Fetch candle data
    candle_response = await get_candles(symbol, timeframe=timeframe, count=count)
    if "error" in candle_response:
        return candle_response

    candles = candle_response.get("candles", [])

    # Run analysis in executor (CPU-bound)
    loop = asyncio.get_event_loop()
    analysis = await loop.run_in_executor(
        None,
        ta_service.analyze,
        symbol,
        timeframe,
        candles,
    )

    return analysis
