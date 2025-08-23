"""Shared data models for the backtests package."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class BacktestConfig(BaseModel):
    """Configuration for backtest runs."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    strategy_name: str = Field(..., description="Strategy class name")
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    timeframe: str = Field(..., description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)")
    start_date: datetime = Field(..., description="Start date for backtest")
    end_date: datetime = Field(..., description="End date for backtest")
    initial_cash: float = Field(default=10000.0, description="Initial capital")
    commission: float = Field(default=0.001, description="Commission rate")
    slippage: float = Field(default=0.0001, description="Slippage percentage")
    random_seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")
    leverage: float = Field(default=1.0, description="Leverage multiplier")
    funding_rate: float = Field(default=0.0001, description="Funding rate per 8h")


class BacktestResult(BaseModel):
    """Results from a backtest run."""
    
    id: str = Field(..., description="Unique backtest ID")
    config: BacktestConfig = Field(..., description="Backtest configuration")
    start_time: datetime = Field(..., description="When backtest started")
    end_time: datetime = Field(..., description="When backtest completed")
    duration: float = Field(..., description="Execution time in seconds")
    final_value: float = Field(..., description="Final portfolio value")
    total_return: float = Field(..., description="Total return percentage")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    total_trades: int = Field(..., description="Total number of trades")
    win_rate: float = Field(..., description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor")
    avg_trade: float = Field(..., description="Average trade P&L")
    max_consecutive_losses: int = Field(..., description="Maximum consecutive losses")
    status: str = Field(default="completed", description="Backtest status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
