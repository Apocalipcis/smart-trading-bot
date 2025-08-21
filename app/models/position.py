"""Position data model for execution foundation."""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class PositionSide(str, Enum):
    """Position side."""
    LONG = 'LONG'
    SHORT = 'SHORT'


class Position(BaseModel):
    """Position model."""
    
    id: str = Field(..., description='Unique position identifier')
    symbol: str = Field(..., description='Trading pair symbol')
    side: PositionSide = Field(..., description='Position side')
    
    # Position details
    quantity: float = Field(..., description='Position quantity')
    entry_price: float = Field(..., description='Average entry price')
    current_price: float = Field(..., description='Current market price')
    
    # Risk management
    stop_loss: Optional[float] = Field(None, description='Stop loss price')
    take_profit: Optional[float] = Field(None, description='Take profit price')
    
    # P&L
    unrealized_pnl: float = Field(0.0, description='Unrealized profit/loss')
    realized_pnl: float = Field(0.0, description='Realized profit/loss')
    
    # Risk metrics
    risk_amount: float = Field(0.0, description='Risk amount in base currency')
    risk_percentage: float = Field(0.0, description='Risk percentage of position')
    
    # Related data
    signal_id: Optional[str] = Field(None, description='Related signal ID')
    order_ids: list[str] = Field(default_factory=list, description='Related order IDs')
    
    # Status
    is_open: bool = Field(True, description='Whether position is open')
    opened_at: datetime = Field(..., description='Position opening timestamp')
    closed_at: Optional[datetime] = Field(None, description='Position closing timestamp')
    
    # Notes
    notes: Optional[str] = Field(None, description='Position notes')
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description='Record creation timestamp')
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __str__(self) -> str:
        return f"{self.symbol}_{self.side}_{self.id}"
    
    def __repr__(self) -> str:
        return f"Position(symbol='{self.symbol}', side='{self.side}', quantity={self.quantity}, pnl={self.unrealized_pnl})"
    
    @property
    def total_pnl(self) -> float:
        """Total profit/loss (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def pnl_percentage(self) -> float:
        """P&L as percentage of entry value."""
        if self.entry_price == 0:
            return 0.0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
