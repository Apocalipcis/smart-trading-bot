"""Candle data model for OHLCV data."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Candle(BaseModel):
    """OHLCV candle data model."""
    
    symbol: str = Field(..., description='Trading pair symbol')
    timeframe: str = Field(..., description='Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)')
    timestamp: datetime = Field(..., description='Candle open timestamp (UTC)')
    open: float = Field(..., description='Opening price')
    high: float = Field(..., description='Highest price during the period')
    low: float = Field(..., description='Lowest price during the period')
    close: float = Field(..., description='Closing price')
    volume: float = Field(..., description='Trading volume')
    
    # Additional calculated fields
    body_size: Optional[float] = Field(None, description='Absolute difference between open and close')
    upper_shadow: Optional[float] = Field(None, description='High minus max(open, close)')
    lower_shadow: Optional[float] = Field(None, description='Min(open, close) minus low')
    is_bullish: Optional[bool] = Field(None, description='True if close > open')
    is_bearish: Optional[bool] = Field(None, description='True if close < open')
    is_doji: Optional[bool] = Field(None, description='True if open ≈ close')
    
    # Metadata
    source: str = Field('binance', description='Data source')
    created_at: datetime = Field(default_factory=datetime.utcnow, description='Record creation timestamp')
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __str__(self) -> str:
        return f"{self.symbol}_{self.timeframe}_{self.timestamp.isoformat()}"
    
    def __repr__(self) -> str:
        return f"Candle(symbol='{self.symbol}', timeframe='{self.timeframe}', timestamp='{self.timestamp}', close={self.close})"
