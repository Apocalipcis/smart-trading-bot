"""Pydantic models for API schemas."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
import re

from pydantic import BaseModel, Field, field_validator, model_validator


class TradingPair(BaseModel):
    """Trading pair model."""
    id: UUID = Field(default_factory=uuid4, description="Unique trading pair ID")
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    base_asset: Optional[str] = Field(None, description="Base asset (e.g., BTC)")
    quote_asset: Optional[str] = Field(None, description="Quote asset (e.g., USDT)")
    strategy: str = Field(..., description="Strategy name (e.g., SMC)")
    is_active: bool = Field(default=True, description="Whether the pair is active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SignalSide(str, Enum):
    """Signal side enumeration."""
    BUY = "buy"
    SELL = "sell"


class Signal(BaseModel):
    """Trading signal model."""
    id: UUID = Field(..., description="Unique signal ID")
    pair: str = Field(..., description="Trading pair")
    side: SignalSide = Field(..., description="Signal side")
    entry_price: Decimal = Field(..., description="Entry price")
    stop_loss: Decimal = Field(..., description="Stop loss price")
    take_profit: Decimal = Field(..., description="Take profit price")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence (0-1)")
    strategy: str = Field(..., description="Strategy name")
    timeframe: str = Field(..., description="Timeframe")
    timestamp: datetime = Field(..., description="Signal timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class TimeframeRole(str, Enum):
    """Timeframe role enumeration."""
    HTF = "HTF"  # Higher Timeframe
    LTF = "LTF"  # Lower Timeframe


class TimeframeConstraint(BaseModel):
    """Timeframe role constraint model."""
    role: TimeframeRole = Field(..., description="Role type")
    min_timeframe: str = Field(..., description="Minimum allowed timeframe for this role")
    max_timeframe: str = Field(..., description="Maximum allowed timeframe for this role")
    description: str = Field(..., description="Constraint description")

    @field_validator('min_timeframe', 'max_timeframe')
    @classmethod
    def validate_timeframe_format(cls, v):
        """Validate timeframe format (e.g., 1m, 5m, 15m, 1h, 4h, 1d)."""
        if not re.match(r'^(\d+)(m|h|d)$', v):
            raise ValueError('Timeframe must be in format: <number><unit> (e.g., 1m, 5m, 15m, 1h, 4h, 1d)')
        return v


class StrategyMetadata(BaseModel):
    """Strategy metadata including role requirements."""
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")
    version: str = Field(..., description="Strategy version")
    required_roles: List[TimeframeRole] = Field(default_factory=list, description="Required roles for this strategy")
    role_constraints: List[TimeframeConstraint] = Field(default_factory=list, description="Role constraints")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")

    @field_validator('required_roles')
    @classmethod
    def validate_required_roles(cls, v):
        """Validate that required roles are unique."""
        if len(set(v)) != len(v):
            raise ValueError('Required roles must be unique')
        return v

    @field_validator('role_constraints')
    @classmethod
    def validate_role_constraints(cls, v):
        """Validate role constraints are consistent."""
        role_constraints = {}
        for constraint in v:
            if constraint.role in role_constraints:
                raise ValueError(f'Multiple constraints defined for role {constraint.role}')
            role_constraints[constraint.role] = constraint
        return v


class PairValidationRequest(BaseModel):
    """Request model for pair validation."""
    symbol: str = Field(..., description="Trading pair symbol to validate")


class PairValidationResponse(BaseModel):
    """Response model for pair validation."""
    is_valid: bool = Field(..., description="Whether the pair is valid on Binance")
    symbol: str = Field(..., description="The validated symbol")


class BacktestRequest(BaseModel):
    """Backtest request model with support for multiple timeframes and roles."""
    pairs: Optional[List[str]] = Field(None, description="Trading pairs")
    strategy: str = Field(..., description="Strategy name")
    timeframes: Optional[List[str]] = Field(None, description="List of timeframes")
    tf_roles: Optional[Dict[str, TimeframeRole]] = Field(None, description="Timeframe to role mapping")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    initial_balance: float = Field(default=10000.0, description="Initial balance")
    risk_per_trade: float = Field(default=2.0, description="Risk per trade percentage")
    leverage: float = Field(default=1.0, description="Leverage")
    
    # Legacy support fields
    pair: Optional[str] = Field(None, description="Legacy single pair field")
    timeframe: Optional[str] = Field(None, description="Legacy single timeframe field")
    initial_capital: Optional[float] = Field(None, description="Legacy initial capital field")
    commission: Optional[float] = Field(None, description="Commission rate")
    slippage: Optional[float] = Field(None, description="Slippage rate")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @field_validator('timeframes')
    @classmethod
    def validate_timeframes(cls, v):
        if v is None:
            return v  # Allow None for legacy compatibility
        if not v:
            raise ValueError('At least one timeframe must be specified')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate timeframes are not allowed')
        
        # Validate timeframe format
        for tf in v:
            if not re.match(r'^(\d+)(m|h|d)$', tf):
                raise ValueError(f'Invalid timeframe format: {tf}. Must be in format: <number><unit> (e.g., 1m, 5m, 15m, 1h, 4h, 1d)')
        
        return v

    @field_validator('tf_roles')
    @classmethod
    def validate_tf_roles(cls, v, info):
        if v is None:
            return v  # Allow None for legacy compatibility
        if 'timeframes' in info.data:
            timeframes = info.data['timeframes']
            if timeframes is None:
                return v  # Allow None for legacy compatibility
            # Ensure all timeframes have roles assigned
            for tf in timeframes:
                if tf not in v:
                    raise ValueError(f'Timeframe {tf} must have a role assigned')
            # Ensure no extra roles for non-existent timeframes
            for tf in v.keys():
                if tf not in timeframes:
                    raise ValueError(f'Role assigned for non-existent timeframe {tf}')
        return v

    @field_validator('risk_per_trade')
    @classmethod
    def validate_risk_per_trade(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Risk per trade must be between 0 and 100')
        return v

    @field_validator('leverage')
    @classmethod
    def validate_leverage(cls, v):
        if v < 1 or v > 125:
            raise ValueError('Leverage must be between 1 and 125')
        return v

    @field_validator('pairs')
    @classmethod
    def validate_pairs(cls, v):
        if v is None:
            return v  # Allow None for legacy compatibility
        if not v:
            raise ValueError('At least one trading pair must be specified')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate trading pairs are not allowed')
        return v

    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v):
        if not v or not v.strip():
            raise ValueError('Strategy name must not be empty')
        return v.strip()

    @model_validator(mode='before')
    @classmethod
    def validate_legacy_compatibility(cls, data):
        """Validate that either new fields or legacy fields are provided."""
        if isinstance(data, dict):
            # Check if new fields are provided
            has_new_fields = (data.get('pairs') is not None and 
                            data.get('timeframes') is not None and 
                            data.get('tf_roles') is not None)
            
            # Check if legacy fields are provided
            has_legacy_fields = (data.get('pair') is not None and 
                               data.get('timeframe') is not None)
            
            if not has_new_fields and not has_legacy_fields:
                raise ValueError('Either new fields (pairs, timeframes, tf_roles) or legacy fields (pair, timeframe) must be provided')
            
            if has_new_fields and has_legacy_fields:
                raise ValueError('Cannot mix new fields (pairs, timeframes, tf_roles) with legacy fields (pair, timeframe)')
        
        return data


class BacktestResult(BaseModel):
    """Backtest result model."""
    id: UUID = Field(..., description="Unique backtest ID")
    pairs: List[str] = Field(..., description="Trading pairs")
    strategy: str = Field(..., description="Strategy name")
    timeframes: List[str] = Field(..., description="List of timeframes used")
    tf_roles: Dict[str, TimeframeRole] = Field(..., description="Timeframe to role mapping used")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    initial_balance: float = Field(..., description="Initial balance")
    final_balance: float = Field(..., description="Final balance")
    total_return: float = Field(..., description="Total return percentage")
    win_rate: float = Field(..., description="Win rate percentage")
    total_trades: int = Field(..., description="Total number of trades")
    profitable_trades: int = Field(..., description="Number of profitable trades")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    artifacts_path: Optional[str] = Field(None, description="Path to artifacts")
    
    # Legacy support fields
    pair: Optional[str] = Field(None, description="Legacy single pair field")
    timeframe: Optional[str] = Field(None, description="Legacy single timeframe field")
    initial_capital: Optional[float] = Field(None, description="Legacy initial capital field")


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderRequest(BaseModel):
    """Order request model."""
    pair: str = Field(..., description="Trading pair")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order type")
    quantity: Optional[float] = Field(None, description="Order quantity")
    price: Optional[float] = Field(None, description="Order price")
    stop_price: Optional[float] = Field(None, description="Stop price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    risk_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Risk percentage")
    leverage: Optional[int] = Field(None, ge=1, le=125, description="Leverage")


class Order(BaseModel):
    """Order model."""
    id: UUID = Field(..., description="Unique order ID")
    exchange_order_id: Optional[str] = Field(None, description="Exchange order ID")
    pair: str = Field(..., description="Trading pair")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order type")
    quantity: float = Field(..., description="Order quantity")
    price: Optional[float] = Field(None, description="Order price")
    status: str = Field(..., description="Order status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Settings(BaseModel):
    """Application settings model."""
    trading_enabled: bool = Field(default=False, description="Whether trading is enabled")
    order_confirmation_required: bool = Field(default=True, description="Whether order confirmation is required")
    max_open_positions: int = Field(default=5, description="Maximum number of open positions")
    risk_per_trade: float = Field(default=2.0, ge=0.0, le=100.0, description="Risk per trade (%)")
    default_leverage: int = Field(default=1, ge=1, le=125, description="Default leverage for futures trading")
    telegram_enabled: bool = Field(default=False, description="Whether Telegram notifications are enabled")
    telegram_bot_token: Optional[str] = Field(None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")
    # Backend-specific fields
    max_risk_per_trade: float = Field(default=2.0, ge=0.0, le=100.0, description="Maximum risk per trade (%)")
    min_risk_reward_ratio: float = Field(default=3.0, ge=1.0, description="Minimum risk-reward ratio")
    debug_mode: bool = Field(default=False, description="Whether debug mode is enabled")


class HealthStatus(BaseModel):
    """Health check status model."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Uptime in seconds")
    database_connected: bool = Field(..., description="Database connection status")
    exchange_connected: bool = Field(..., description="Exchange connection status")


class NotificationRequest(BaseModel):
    """Notification request model."""
    message: str = Field(..., description="Message to send")
    notification_type: str = Field(default="test", description="Notification type")


class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class AvailableTimeframe(BaseModel):
    """Available timeframe model."""
    timeframe: str = Field(..., description="Timeframe string (e.g., 1m, 5m, 15m, 1h, 4h, 1d)")
    description: str = Field(..., description="Human-readable description")
    minutes: int = Field(..., description="Duration in minutes")
    supported_roles: List[TimeframeRole] = Field(..., description="Supported roles for this timeframe")
    is_active: bool = Field(default=True, description="Whether this timeframe is available")


class AvailableTimeframes(BaseModel):
    """Available timeframes response model."""
    timeframes: List[AvailableTimeframe] = Field(..., description="List of available timeframes")
    default_htf: str = Field(default="1h", description="Default higher timeframe")
    default_ltf: str = Field(default="15m", description="Default lower timeframe")
    role_constraints: List[TimeframeConstraint] = Field(..., description="Role constraints")


class StrategyInfo(BaseModel):
    """Strategy information model."""
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")
    version: str = Field(..., description="Strategy version")
    required_roles: List[TimeframeRole] = Field(default_factory=list, description="Required roles for this strategy")
    role_constraints: List[TimeframeConstraint] = Field(default_factory=list, description="Role constraints")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    is_active: bool = Field(default=True, description="Whether this strategy is available")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
