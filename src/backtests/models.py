"""Shared data models for the backtests package."""

from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field, field_validator


class BacktestConfig(BaseModel):
    """Configuration for backtest runs."""
    
    symbol: str = Field(..., description="Trading pair symbol")
    strategy_name: str = Field(..., description="Strategy class name")
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    
    # Primary timeframe fields (new multi-timeframe support)
    timeframes: Optional[List[str]] = Field(None, description="List of timeframes for multi-timeframe strategies")
    tf_roles: Optional[Dict[str, str]] = Field(None, description="Timeframe to role mapping (HTF/LTF)")
    
    # Legacy single timeframe field (maintained for backwards compatibility)
    timeframe: Optional[str] = Field(None, description="Legacy single timeframe (use 'timeframes' for multi-timeframe)")
    
    start_date: datetime = Field(..., description="Start date for backtest")
    end_date: datetime = Field(..., description="End date for backtest")
    initial_cash: float = Field(default=10000.0, description="Initial capital")
    commission: float = Field(default=0.001, description="Commission rate")
    slippage: float = Field(default=0.0001, description="Slippage percentage")
    random_seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")
    leverage: float = Field(default=1.0, description="Leverage multiplier")
    funding_rate: float = Field(default=0.0001, description="Funding rate per 8h")
    
    @field_validator('timeframes')
    @classmethod
    def validate_timeframes(cls, v):
        """Validate timeframes if provided."""
        if v is not None:
            if not v:
                raise ValueError('Timeframes list cannot be empty')
            if len(set(v)) != len(v):
                raise ValueError('Duplicate timeframes are not allowed')
            
            # Validate timeframe format
            import re
            for tf in v:
                if not re.match(r'^(\d+)(m|h|d|w|M)$', tf):
                    raise ValueError(f'Invalid timeframe format: {tf}. Use format like 1m, 5m, 1h, 4h, 1d')
        return v
    
    @field_validator('tf_roles')
    @classmethod
    def validate_tf_roles(cls, v, info):
        """Validate timeframe roles if provided."""
        if v is not None:
            timeframes = info.data.get('timeframes')
            if timeframes:
                # Check that all timeframes have roles assigned
                missing_roles = set(timeframes) - set(v.keys())
                if missing_roles:
                    raise ValueError(f'Missing role assignments for timeframes: {missing_roles}')
                
                # Check that all roles are valid
                valid_roles = {'HTF', 'LTF'}
                invalid_roles = set(v.values()) - valid_roles
                if invalid_roles:
                    raise ValueError(f'Invalid roles: {invalid_roles}. Valid roles are: {valid_roles}')
        return v
    
    def get_primary_timeframes(self) -> List[str]:
        """Get the primary timeframes to use for the backtest."""
        if self.timeframes:
            return self.timeframes
        elif self.timeframe:
            return [self.timeframe]
        else:
            raise ValueError("No timeframes specified in BacktestConfig")
    
    def get_primary_timeframe(self) -> str:
        """Get the primary timeframe (for backwards compatibility)."""
        timeframes = self.get_primary_timeframes()
        return timeframes[0] if timeframes else None


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
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed trade history")
    status: str = Field(default="completed", description="Backtest status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
