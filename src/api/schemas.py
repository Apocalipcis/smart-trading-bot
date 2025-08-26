"""Pydantic models for API schemas."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TradingPair(BaseModel):
    """Trading pair model."""
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    base_asset: str = Field(..., description="Base asset (e.g., BTC)")
    quote_asset: str = Field(..., description="Quote asset (e.g., USDT)")
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


class BacktestRequest(BaseModel):
    """Backtest request model."""
    pair: str = Field(..., description="Trading pair")
    strategy: str = Field(..., description="Strategy name")
    timeframe: str = Field(..., description="Timeframe")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    initial_capital: float = Field(default=10000.0, description="Initial capital")
    commission: float = Field(default=0.001, description="Commission rate")
    slippage: float = Field(default=0.0001, description="Slippage rate")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v


class BacktestResult(BaseModel):
    """Backtest result model."""
    id: UUID = Field(..., description="Unique backtest ID")
    pair: str = Field(..., description="Trading pair")
    strategy: str = Field(..., description="Strategy name")
    timeframe: str = Field(..., description="Timeframe")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    initial_capital: float = Field(..., description="Initial capital")
    final_capital: float = Field(..., description="Final capital")
    total_return: float = Field(..., description="Total return percentage")
    win_rate: float = Field(..., description="Win rate percentage")
    total_trades: int = Field(..., description="Total number of trades")
    profitable_trades: int = Field(..., description="Number of profitable trades")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    artifacts_path: Optional[str] = Field(None, description="Path to artifacts")


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
