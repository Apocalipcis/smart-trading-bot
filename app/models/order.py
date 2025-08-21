"""Order data model for execution foundation."""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class OrderType(str, Enum):
    """Order types."""
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    STOP_MARKET = 'STOP_MARKET'
    STOP_LIMIT = 'STOP_LIMIT'
    TAKE_PROFIT_MARKET = 'TAKE_PROFIT_MARKET'
    TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = 'PENDING'
    PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    FILLED = 'FILLED'
    CANCELLED = 'CANCELLED'
    REJECTED = 'REJECTED'
    EXPIRED = 'EXPIRED'


class OrderRequest(BaseModel):
    """Order request model."""
    
    id: str = Field(..., description='Unique order identifier')
    symbol: str = Field(..., description='Trading pair symbol')
    side: str = Field(..., description='Order side (BUY/SELL)')
    order_type: OrderType = Field(..., description='Order type')
    
    # Quantity and price
    quantity: float = Field(..., description='Order quantity')
    price: Optional[float] = Field(None, description='Order price (required for limit orders)')
    
    # Stop loss and take profit
    stop_loss: Optional[float] = Field(None, description='Stop loss price')
    take_profit: Optional[float] = Field(None, description='Take profit price')
    
    # Time in force
    time_in_force: str = Field('GTC', description='Time in force (GTC, IOC, FOK)')
    
    # Related signal
    signal_id: Optional[str] = Field(None, description='Related signal ID')
    
    # Risk management
    max_position_size: Optional[float] = Field(None, description='Maximum position size')
    risk_percentage: Optional[float] = Field(None, description='Risk percentage of account')
    
    # Notes
    notes: Optional[str] = Field(None, description='Order notes')
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description='Order creation timestamp')
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __str__(self) -> str:
        return f"{self.symbol}_{self.side}_{self.order_type}_{self.id}"
    
    def __repr__(self) -> str:
        return f"OrderRequest(symbol='{self.symbol}', side='{self.side}', type='{self.order_type}', quantity={self.quantity})"
