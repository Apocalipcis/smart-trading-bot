"""Orders package for order management and execution."""

__version__ = "1.0.0"

from .sizing import PositionSizer, RiskModel
from .types import (
    Order, MarketOrder, LimitOrder, StopMarketOrder, 
    StopLimitOrder, TrailingStopOrder, OrderStatus, OrderSide
)
from .queue import OrderQueue, OrderSubmissionResult
from .pending import PendingConfirmationStore

__all__ = [
    # Sizing
    "PositionSizer",
    "RiskModel",
    
    # Order types
    "Order",
    "MarketOrder", 
    "LimitOrder",
    "StopMarketOrder",
    "StopLimitOrder", 
    "TrailingStopOrder",
    "OrderStatus",
    "OrderSide",
    
    # Queue and pending
    "OrderQueue",
    "OrderSubmissionResult", 
    "PendingConfirmationStore",
]
