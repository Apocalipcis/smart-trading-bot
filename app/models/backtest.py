"""Backtest data models for backtesting results and trade tracking."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TradeResult(BaseModel):
    """Individual trade result from backtesting."""
    
    id: str = Field(..., description='Unique trade identifier')
    symbol: str = Field(..., description='Trading pair symbol')
    timeframe: str = Field(..., description='Timeframe')
    
    # Signal information
    signal_kind: str = Field(..., description='Type of signal that triggered trade')
    signal_timestamp: datetime = Field(..., description='Signal generation timestamp')
    direction: str = Field(..., description='Trade direction (LONG/SHORT)')
    
    # Entry details
    entry_timestamp: datetime = Field(..., description='Trade entry timestamp')
    entry_price: float = Field(..., description='Entry price')
    stop_loss_price: float = Field(..., description='Stop loss price')
    take_profit_price: float = Field(..., description='Take profit price')
    
    # Exit details
    exit_reason: str = Field(..., description='Reason for exit (SL/TP/Manual)')
    exit_timestamp: datetime = Field(..., description='Trade exit timestamp')
    exit_price: float = Field(..., description='Exit price')
    
    # Performance metrics
    r_multiple: float = Field(..., description='Risk-reward ratio (R-multiple)')
    mae: float = Field(..., description='Maximum Adverse Excursion')
    mfe: float = Field(..., description='Maximum Favorable Excursion')
    
    # Additional data
    notes: Optional[str] = Field(None, description='Trade notes')
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __str__(self) -> str:
        return f"{self.symbol}_{self.signal_kind}_{self.direction}_{self.id}"
    
    def __repr__(self) -> str:
        return f"TradeResult(symbol='{self.symbol}', direction='{self.direction}', r_multiple={self.r_multiple})"


class BacktestResult(BaseModel):
    """Complete backtest result with performance metrics."""
    
    id: str = Field(..., description='Unique backtest identifier')
    symbol: str = Field(..., description='Trading pair symbol')
    timeframe: str = Field(..., description='Timeframe')
    
    # Time period
    start_date: datetime = Field(..., description='Backtest start date')
    end_date: datetime = Field(..., description='Backtest end date')
    
    # Trade statistics
    total_trades: int = Field(0, description='Total number of trades')
    winning_trades: int = Field(0, description='Number of winning trades')
    losing_trades: int = Field(0, description='Number of losing trades')
    
    # Performance metrics
    win_rate: float = Field(0.0, description='Win rate percentage')
    profit_factor: float = Field(0.0, description='Profit factor (gross profit / gross loss)')
    average_r: float = Field(0.0, description='Average R-multiple')
    expectancy: float = Field(0.0, description='Expected value per trade')
    max_drawdown_r: float = Field(0.0, description='Maximum drawdown in R-multiples')
    
    # Risk metrics
    sharpe_like: float = Field(0.0, description='Sharpe-like ratio')
    time_in_market: float = Field(0.0, description='Percentage of time in market')
    
    # Trade details
    trades: List[TradeResult] = Field(default_factory=list, description='Individual trade results')
    
    # Configuration
    parameters: dict = Field(default_factory=dict, description='Backtest parameters used')
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description='Backtest creation timestamp')
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __str__(self) -> str:
        return f"{self.symbol}_{self.timeframe}_{self.start_date.date()}_{self.end_date.date()}"
    
    def __repr__(self) -> str:
        return f"BacktestResult(symbol='{self.symbol}', trades={self.total_trades}, win_rate={self.win_rate:.2f}%)"
    
    @property
    def total_return(self) -> float:
        """Total return from all trades."""
        return sum(trade.r_multiple for trade in self.trades)
    
    @property
    def gross_profit(self) -> float:
        """Gross profit from winning trades."""
        return sum(trade.r_multiple for trade in self.trades if trade.r_multiple > 0)
    
    @property
    def gross_loss(self) -> float:
        """Gross loss from losing trades."""
        return abs(sum(trade.r_multiple for trade in self.trades if trade.r_multiple < 0))
