"""Trading API endpoints for the SMC Signal Service."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.utils.trading_state import trading_state
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def check_trading_enabled():
    """Dependency to check if trading is enabled."""
    if not trading_state.trading_enabled:
        trading_state.log_trade_attempt("API endpoint access", "Trading endpoint accessed while disabled")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Trading disabled",
                "message": trading_state._get_status_message(),
                "trading_enabled": False,
                "mode": trading_state.mode
            }
        )


@router.get("/status")
async def get_trading_status() -> Dict[str, Any]:
    """Get current trading status and capabilities."""
    return trading_state.get_status_info()


@router.post("/place-order")
async def place_order(order_data: Dict[str, Any]):
    """Place a new trading order."""
    # This endpoint is protected by the dependency
    check_trading_enabled()
    
    # Log the order attempt
    trading_state.log_trade_attempt("place_order", f"Order for {order_data.get('symbol', 'unknown')}")
    
    # In a real implementation, this would place the order
    # For now, we just return a success response
    return {
        "message": "Order placed successfully",
        "order_id": "demo_order_123",
        "status": "pending"
    }


@router.post("/close-order")
async def close_order(order_id: str):
    """Close an existing trading order."""
    # This endpoint is protected by the dependency
    check_trading_enabled()
    
    # Log the close attempt
    trading_state.log_trade_attempt("close_order", f"Close order {order_id}")
    
    # In a real implementation, this would close the order
    # For now, we just return a success response
    return {
        "message": "Order closed successfully",
        "order_id": order_id,
        "status": "closed"
    }


@router.get("/positions")
async def get_positions():
    """Get current trading positions."""
    # This endpoint is protected by the dependency
    check_trading_enabled()
    
    # Log the positions access
    trading_state.log_trade_attempt("get_positions", "Accessing trading positions")
    
    # In a real implementation, this would return actual positions
    # For now, we just return an empty list
    return {
        "positions": [],
        "total_count": 0
    }


@router.post("/close-position")
async def close_position(position_id: str):
    """Close a trading position."""
    # This endpoint is protected by the dependency
    check_trading_enabled()
    
    # Log the close attempt
    trading_state.log_trade_attempt("close_position", f"Close position {position_id}")
    
    # In a real implementation, this would close the position
    # For now, we just return a success response
    return {
        "message": "Position closed successfully",
        "position_id": position_id,
        "status": "closed"
    }
