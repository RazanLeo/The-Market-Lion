"""Broker integration router: Capital.com + Exness/MT5."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth import get_current_user
from models.user import User
from services.capital_com import CapitalComService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/broker", tags=["Broker Integration"])

# Per-user session cache: user_id → CapitalComService instance
_sessions: dict[str, CapitalComService] = {}


# ── Schemas ───────────────────────────────────────────────────────────────────

class BrokerConnectRequest(BaseModel):
    broker: str  # "capital_com" | "exness" | "mt5"
    api_key: Optional[str] = None
    identifier: Optional[str] = None
    password: Optional[str] = None
    account_type: str = "demo"  # "demo" | "live"
    account_id: Optional[str] = None


class OrderRequest(BaseModel):
    symbol: str
    side: str  # "buy" | "sell"
    size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    order_type: str = "MARKET"  # "MARKET" | "LIMIT"
    level: Optional[float] = None  # for LIMIT orders


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_user_session(user_id: str) -> Optional[CapitalComService]:
    return _sessions.get(user_id)


def _require_session(user: User) -> CapitalComService:
    svc = _get_user_session(str(user.id))
    if not svc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No broker connected. Call POST /api/broker/connect first.",
        )
    return svc


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/connect")
async def connect_broker(
    body: BrokerConnectRequest,
    current_user: User = Depends(get_current_user),
):
    """Connect a broker account."""
    user_id = str(current_user.id)

    if body.broker == "capital_com":
        demo = body.account_type != "live"
        identifier = body.identifier
        password = body.password
        if not identifier or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Capital.com requires identifier (email) and password",
            )
        try:
            svc = CapitalComService(identifier=identifier, password=password, demo=demo)
            session_data = await svc.create_session()
            _sessions[user_id] = svc
            account_info = await svc.get_account_details()
            return {
                "status": "connected",
                "broker": "capital_com",
                "account_type": body.account_type,
                "account": account_info,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to Capital.com: {str(e)}",
            )

    elif body.broker in ("exness", "mt5"):
        # MT5/Exness: simulate connection (real MT5 requires MetaTrader terminal)
        _sessions[user_id] = None  # Placeholder
        return {
            "status": "connected",
            "broker": body.broker,
            "account_type": body.account_type,
            "message": f"{body.broker.upper()} connected (simulated). MT5 requires terminal integration.",
            "account_id": body.account_id,
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported broker: {body.broker}. Supported: capital_com, exness, mt5",
        )


@router.delete("/disconnect")
async def disconnect_broker(current_user: User = Depends(get_current_user)):
    """Disconnect the current broker session."""
    user_id = str(current_user.id)
    svc = _sessions.pop(user_id, None)
    if svc and hasattr(svc, "close"):
        try:
            await svc.close()
        except Exception:
            pass
    return {"status": "disconnected"}


@router.get("/account")
async def get_account(current_user: User = Depends(get_current_user)):
    """Get broker account balance and info."""
    svc = _require_session(current_user)
    try:
        account_data = await svc.get_account_details()
        return {"broker": "capital_com", "account": account_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch account: {str(e)}",
        )


@router.get("/positions")
async def get_positions(current_user: User = Depends(get_current_user)):
    """Get all open positions."""
    svc = _require_session(current_user)
    try:
        positions_data = await svc.get_positions()
        return {
            "broker": "capital_com",
            "positions": positions_data.get("positions", []),
            "count": len(positions_data.get("positions", [])),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch positions: {str(e)}",
        )


@router.post("/order")
async def place_order(
    body: OrderRequest,
    current_user: User = Depends(get_current_user),
):
    """Place a new trade order."""
    svc = _require_session(current_user)

    epic = CapitalComService.symbol_to_epic(body.symbol)
    if not epic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Symbol {body.symbol} not supported by Capital.com",
        )

    direction = "BUY" if body.side.lower() == "buy" else "SELL"

    try:
        result = await svc.create_order(
            epic=epic,
            direction=direction,
            size=body.size,
            stop_level=body.stop_loss,
            profit_level=body.take_profit,
            order_type=body.order_type.upper(),
            level=body.level,
        )
        return {
            "status": "success",
            "broker": "capital_com",
            "order": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to place order: {str(e)}",
        )


@router.delete("/order/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending order."""
    svc = _require_session(current_user)
    try:
        result = await svc.cancel_order(order_id)
        return {"status": "cancelled", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to cancel order {order_id}: {str(e)}",
        )


@router.delete("/position/{deal_id}")
async def close_position(
    deal_id: str,
    current_user: User = Depends(get_current_user),
):
    """Close an open position."""
    svc = _require_session(current_user)
    try:
        result = await svc.close_position(deal_id)
        return {"status": "closed", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to close position {deal_id}: {str(e)}",
        )
