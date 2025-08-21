"""Signal data model for SMC trading signals."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class SignalKind(str, Enum):
    """Types of SMC signals."""
    BOS = 'BOS'  # Break of Structure
    CHOCH = 'CHOCH'  # Change of Character
    FVG = 'FVG'  # Fair Value Gap
    SWEEP = 'SWEEP'  # Liquidity Sweep
    MITIGATION = 'MITIGATION'  # FVG Mitigation
    ORDERBLOCK = 'ORDERBLOCK'  # Order Block
    EQUILIBRIUM = 'EQUILIBRIUM'  # Equilibrium


class SignalDirection(str, Enum):
    """Signal direction."""
    LONG = 'LONG'
    SHORT = 'SHORT'
    NEUTRAL = 'NEUTRAL'


class Signal(BaseModel):
    """SMC trading signal model."""
    
    id: str = Field(..., description='Unique signal identifier')
    symbol: str = Field(..., description='Trading pair symbol')
    timeframe: str = Field(..., description='Timeframe')
    higher_timeframe: str = Field(..., description='Higher timeframe for context')
    
    # Signal details
    kind: SignalKind = Field(..., description='Type of signal')
    direction: SignalDirection = Field(..., description='Signal direction')
    timestamp: datetime = Field(..., description='Signal generation timestamp')
    
    # Price levels
    entry_price: float = Field(..., description='Entry price')
    stop_loss: float = Field(..., description='Stop loss price')
    take_profit: float = Field(..., description='Take profit price')
    
    # Signal context
    strength: float = Field(..., ge=0.0, le=1.0, description='Signal strength (0-1)')
    confidence: float = Field(..., ge=0.0, le=1.0, description='Confidence level (0-1)')
    
    # Additional data
    volume_confirmation: bool = Field(False, description='Volume confirms signal')
    related_signals: List[str] = Field(default_factory=list, description='Related signal IDs')
    
    # Market context
    support_level: Optional[float] = Field(None, description='Nearby support level')
    resistance_level: Optional[float] = Field(None, description='Nearby resistance level')
    trend_direction: Optional[str] = Field(None, description='Current trend direction')
    
    # Risk metrics
    risk_reward_ratio: Optional[float] = Field(None, description='Risk to reward ratio')
    position_size_suggestion: Optional[float] = Field(None, description='Suggested position size %')
    
    # Notes and analysis
    notes: Optional[str] = Field(None, description='Additional analysis notes')
    
    # Metadata
    source: str = Field('smc_engine', description='Signal source')
    created_at: datetime = Field(default_factory=datetime.utcnow, description='Record creation timestamp')
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __str__(self) -> str:
        return f"{self.symbol}_{self.timeframe}_{self.kind}_{self.direction}_{self.timestamp.isoformat()}"
    
    def __repr__(self) -> str:
        return f"Signal(symbol='{self.symbol}', kind='{self.kind}', direction='{self.direction}', strength={self.strength})"
