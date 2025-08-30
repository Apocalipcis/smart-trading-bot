"""Order types and status management."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator, validator


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class Order(BaseModel):
    """Base order class with common properties."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exchange_order_id: Optional[str] = Field(None, description="Exchange order ID")
    pair: str = Field(..., description="Trading pair")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order type")
    quantity: Decimal = Field(..., description="Order quantity")
    price: Optional[Decimal] = Field(None, description="Order price")
    stop_price: Optional[Decimal] = Field(None, description="Stop price")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filled_at: Optional[datetime] = Field(None, description="When order was filled")
    filled_quantity: Decimal = Field(default=Decimal('0'), description="Filled quantity")
    average_price: Optional[Decimal] = Field(None, description="Average fill price")
    commission: Decimal = Field(default=Decimal('0'), description="Commission paid")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('quantity', 'price', 'stop_price', 'filled_quantity', 'commission', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        """Convert to Decimal if string or float."""
        if v is None:
            return v
        return Decimal(str(v))
    
    @field_validator('quantity', 'filled_quantity')
    @classmethod
    def validate_positive_quantity(cls, v):
        """Ensure quantity is positive."""
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v
    
    @field_validator('price', 'stop_price')
    @classmethod
    def validate_positive_price(cls, v):
        """Ensure price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        return v
    
    def update_status(self, status: OrderStatus, **kwargs) -> None:
        """Update order status and related fields."""
        self.status = status
        self.updated_at = datetime.now(timezone.utc)
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    def is_cancelled(self) -> bool:
        """Check if order is cancelled."""
        return self.status in [OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]
    
    def get_remaining_quantity(self) -> Decimal:
        """Get remaining unfilled quantity."""
        return self.quantity - self.filled_quantity
    
    def get_fill_percentage(self) -> float:
        """Get fill percentage as float."""
        if self.quantity == 0:
            return 0.0
        return float(self.filled_quantity / self.quantity * 100)
    
    model_config = {
        "json_encoders": {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    }


class MarketOrder(Order):
    """Market order implementation."""
    
    order_type: OrderType = Field(default=OrderType.MARKET)
    price: Optional[Decimal] = Field(None, description="Market orders don't have a price")
    
    @field_validator('price')
    @classmethod
    def validate_market_price(cls, v):
        """Market orders should not have a price."""
        if v is not None:
            raise ValueError("Market orders cannot have a price")
        return None


class LimitOrder(Order):
    """Limit order implementation."""
    
    order_type: OrderType = Field(default=OrderType.LIMIT)
    price: Decimal = Field(..., description="Limit price")
    time_in_force: str = Field(default="GTC", description="Time in force")
    
    @field_validator('price')
    @classmethod
    def validate_limit_price(cls, v):
        """Limit orders must have a price."""
        if v is None:
            raise ValueError("Limit orders must have a price")
        return v


class StopMarketOrder(Order):
    """Stop market order implementation."""
    
    order_type: OrderType = Field(default=OrderType.STOP_MARKET)
    stop_price: Decimal = Field(..., description="Stop price")
    price: Optional[Decimal] = Field(None, description="Stop market orders don't have a price")
    
    @field_validator('stop_price')
    @classmethod
    def validate_stop_price(cls, v):
        """Stop orders must have a stop price."""
        if v is None:
            raise ValueError("Stop orders must have a stop price")
        return v
    
    @field_validator('price')
    @classmethod
    def validate_stop_market_price(cls, v):
        """Stop market orders should not have a price."""
        if v is not None:
            raise ValueError("Stop market orders cannot have a price")
        return None


class StopLimitOrder(Order):
    """Stop limit order implementation."""
    
    order_type: OrderType = Field(default=OrderType.STOP_LIMIT)
    stop_price: Decimal = Field(..., description="Stop price")
    price: Decimal = Field(..., description="Limit price")
    
    @field_validator('stop_price', 'price')
    @classmethod
    def validate_stop_limit_prices(cls, v, info):
        """Validate stop and limit prices."""
        if v is None:
            raise ValueError("Stop limit orders must have both stop and limit prices")
        return v


class TrailingStopOrder(Order):
    """Trailing stop order implementation."""
    
    order_type: OrderType = Field(default=OrderType.TRAILING_STOP)
    stop_price: Decimal = Field(..., description="Initial stop price")
    trailing_percent: Optional[Decimal] = Field(None, description="Trailing percentage")
    trailing_distance: Optional[Decimal] = Field(None, description="Trailing distance")
    activation_price: Optional[Decimal] = Field(None, description="Activation price")
    
    @field_validator('trailing_percent', 'trailing_distance')
    @classmethod
    def validate_trailing_params(cls, v, info):
        """Validate trailing parameters."""
        if v is not None and v <= 0:
            raise ValueError("Trailing parameters must be positive")
        return v
    
    def update_trailing_stop(self, current_price: Decimal) -> bool:
        """Update trailing stop based on current price."""
        if self.trailing_percent is not None:
            # Percentage-based trailing
            if self.side == OrderSide.BUY:
                new_stop = current_price * (1 - self.trailing_percent / 100)
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
                    self.updated_at = datetime.now(timezone.utc)
                    return True
            else:  # SELL
                new_stop = current_price * (1 + self.trailing_percent / 100)
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
                    self.updated_at = datetime.now(timezone.utc)
                    return True
                
        elif self.trailing_distance is not None:
            # Distance-based trailing
            if self.side == OrderSide.BUY:
                new_stop = current_price - self.trailing_distance
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
                    self.updated_at = datetime.now(timezone.utc)
                    return True
            else:  # SELL
                new_stop = current_price + self.trailing_distance
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
                    self.updated_at = datetime.now(timezone.utc)
                    return True
        
        return False
