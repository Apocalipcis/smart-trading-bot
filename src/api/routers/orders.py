"""Orders router for order management (trading mode only)."""

from typing import List, Optional
from uuid import uuid4
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import require_trading_enabled, require_read_access, require_simulation_or_trading_enabled
from ..schemas import APIResponse, Order, OrderRequest, PaginatedResponse

router = APIRouter(prefix="/orders", tags=["orders"])

# In-memory storage for orders (will be replaced with database)
_orders: List[Order] = []


@router.get("/", response_model=PaginatedResponse)
async def get_orders(
    pair: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> PaginatedResponse:
    """Get all orders with optional filtering and pagination."""
    # Filter orders
    filtered_orders = _orders.copy()
    
    if pair:
        filtered_orders = [o for o in filtered_orders if o.pair.upper() == pair.upper()]
    
    if status:
        filtered_orders = [o for o in filtered_orders if o.status.lower() == status.lower()]
    
    # Sort by creation date (newest first)
    filtered_orders.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply pagination
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    total = len(filtered_orders)
    items = filtered_orders[start_idx:end_idx]
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/pending")
async def get_pending_orders(
    simulation_or_trading_enabled: bool = Depends(require_simulation_or_trading_enabled)
):
    """Get pending orders (alias for pending/confirmation)."""
    # Return orders with "pending" status
    pending_orders = [o for o in _orders if o.status == "pending"]
    
    # Transform to match frontend expectations
    transformed_orders = []
    for order in pending_orders:
        # Extract metadata for pending confirmation structure
        metadata = order.metadata or {}
        transformed_orders.append({
            "id": str(order.id),
            "signal_id": getattr(order, 'signal_id', ''),
            "pair_id": order.pair,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": order.price,
            "stop_loss": metadata.get('stop_loss', 0),
            "take_profit": metadata.get('take_profit', 0),
            "created_at": order.created_at.isoformat(),
            "expires_at": (order.created_at + timedelta(minutes=5)).isoformat()  # 5 minute TTL
        })
    
    return transformed_orders


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> Order:
    """Get a specific order by ID."""
    for order in _orders:
        if str(order.id) == order_id:
            return order
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Order {order_id} not found"
    )


@router.post("/", response_model=Order)
async def create_order(
    order_request: OrderRequest,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> Order:
    """Create a new order."""
    # Generate order ID
    order_id = uuid4()
    
    # TODO: This is a placeholder implementation
    # In the actual implementation, this would:
    # 1. Validate the order request
    # 2. Calculate position size based on risk percentage
    # 3. Submit order to exchange
    # 4. Handle order confirmation if required
    
    # Placeholder order creation
    order = Order(
        id=order_id,
        pair=order_request.pair,
        side=order_request.side,
        order_type=order_request.order_type,
        quantity=order_request.quantity or 0.001,  # Default quantity
        price=order_request.price,
        status="pending",  # Will be updated based on exchange response
        metadata={
            "stop_price": order_request.stop_price,
            "take_profit": order_request.take_profit,
            "stop_loss": order_request.stop_loss,
            "risk_percentage": order_request.risk_percentage,
            "leverage": order_request.leverage
        }
    )
    
    # Add to storage
    _orders.append(order)
    
    return order


@router.put("/{order_id}/cancel", response_model=APIResponse)
async def cancel_order(
    order_id: str,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> APIResponse:
    """Cancel an order."""
    for order in _orders:
        if str(order.id) == order_id:
            if order.status == "cancelled":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order {order_id} is already cancelled"
                )
            
            # TODO: This would cancel the order on the exchange
            # For now, just update the status
            order.status = "cancelled"
            
            return APIResponse(
                success=True,
                message=f"Order {order_id} cancelled successfully"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Order {order_id} not found"
    )


@router.delete("/{order_id}", response_model=APIResponse)
async def delete_order(
    order_id: str,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> APIResponse:
    """Delete an order."""
    for i, order in enumerate(_orders):
        if str(order.id) == order_id:
            _orders.pop(i)
            return APIResponse(
                success=True,
                message=f"Order {order_id} deleted successfully"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Order {order_id} not found"
    )


@router.get("/pending/confirmation")
async def get_pending_confirmations(
    trading_enabled: bool = Depends(require_trading_enabled)
):
    """Get orders pending confirmation."""
    # TODO: This would query the pending confirmation store
    # For now, return orders with "pending" status
    pending_orders = [o for o in _orders if o.status == "pending"]
    
    return {
        "pending_orders": pending_orders,
        "count": len(pending_orders)
    }


@router.post("/{order_id}/confirm")
async def confirm_order(
    order_id: str,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> APIResponse:
    """Confirm a pending order."""
    for order in _orders:
        if str(order.id) == order_id:
            if order.status != "pending":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order {order_id} is not pending confirmation"
                )
            
            # TODO: This would submit the order to the exchange
            # For now, just update the status
            order.status = "confirmed"
            
            return APIResponse(
                success=True,
                message=f"Order {order_id} confirmed and submitted to exchange"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Order {order_id} not found"
    )


@router.post("/pending/{order_id}/confirm")
async def confirm_pending_order(
    order_id: str,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> APIResponse:
    """Confirm a pending order (frontend endpoint)."""
    for order in _orders:
        if str(order.id) == order_id:
            if order.status != "pending":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order {order_id} is not pending confirmation"
                )
            
            # TODO: This would submit the order to the exchange
            # For now, just update the status
            order.status = "confirmed"
            
            return APIResponse(
                success=True,
                message=f"Order {order_id} confirmed and submitted to exchange"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Order {order_id} not found"
    )


@router.post("/pending/{order_id}/reject")
async def reject_pending_order(
    order_id: str,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> APIResponse:
    """Reject a pending order."""
    for order in _orders:
        if str(order.id) == order_id:
            if order.status != "pending":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order {order_id} is not pending confirmation"
                )
            
            # Update the status to rejected
            order.status = "rejected"
            
            return APIResponse(
                success=True,
                message=f"Order {order_id} rejected"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Order {order_id} not found"
    )


@router.get("/stats/summary")
async def get_order_stats(
    trading_enabled: bool = Depends(require_trading_enabled)
):
    """Get order statistics."""
    if not _orders:
        return {
            "total_orders": 0,
            "orders_today": 0,
            "orders_this_week": 0,
            "by_status": {},
            "by_side": {"buy": 0, "sell": 0},
            "by_pair": {}
        }
    
    from datetime import datetime, timedelta, timezone
    
    now = datetime.now(timezone.utc)
    today = now.date()
    week_ago = now - timedelta(days=7)
    
    orders_today = [o for o in _orders if o.created_at.date() == today]
    orders_this_week = [o for o in _orders if o.created_at >= week_ago]
    
    by_status = {}
    by_side = {"buy": 0, "sell": 0}
    by_pair = {}
    
    for order in _orders:
        # Count by status
        status = order.status
        by_status[status] = by_status.get(status, 0) + 1
        
        # Count by side
        by_side[order.side.value] += 1
        
        # Count by pair
        pair = order.pair
        by_pair[pair] = by_pair.get(pair, 0) + 1
    
    return {
        "total_orders": len(_orders),
        "orders_today": len(orders_today),
        "orders_this_week": len(orders_this_week),
        "by_status": by_status,
        "by_side": by_side,
        "by_pair": by_pair
    }


@router.get("/positions/open")
async def get_open_positions(
    trading_enabled: bool = Depends(require_trading_enabled)
):
    """Get currently open positions."""
    # TODO: This would query the exchange for actual positions
    # For now, return a placeholder response
    return {
        "positions": [],
        "total_pnl": 0.0,
        "total_margin_used": 0.0
    }


@router.post("/positions/close/{pair}")
async def close_position(
    pair: str,
    trading_enabled: bool = Depends(require_trading_enabled)
) -> APIResponse:
    """Close an open position for a specific pair."""
    # TODO: This would submit a closing order to the exchange
    return APIResponse(
        success=True,
        message=f"Position for {pair} closed successfully"
    )
