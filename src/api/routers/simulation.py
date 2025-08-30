"""Simulation API endpoints."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..dependencies import require_read_access
from ..schemas import APIResponse, PaginatedResponse
from src.simulation.engine import SimulationEngine
from src.simulation.portfolio import Position, Trade, PortfolioSnapshot
from src.simulation.config import SimulationConfig
from src.orders.types import Order, OrderStatus
from src.orders.adapters import OrdersAdapter, OrdersAdapterFactory
from src.config.trading import TradingConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Global simulation engine instance
_simulation_engine: Optional[SimulationEngine] = None
_trading_config: Optional[TradingConfig] = None
_orders_adapter: Optional[OrdersAdapter] = None


# Pydantic models for API responses
class SimulationStatus(BaseModel):
    """Simulation engine status."""
    running: bool = Field(..., description="Whether simulation engine is running")
    mode: str = Field(..., description="Current trading mode")
    portfolio_value: float = Field(..., description="Current portfolio value")
    positions_count: int = Field(..., description="Number of open positions")
    orders_count: int = Field(..., description="Total number of orders")
    stats: Dict[str, Any] = Field(..., description="Simulation statistics")


class SimulationPortfolio(BaseModel):
    """Simulation portfolio information."""
    total_value: float = Field(..., description="Total portfolio value")
    cash: float = Field(..., description="Available cash")
    positions_value: float = Field(..., description="Value of all positions")
    unrealized_pnl: float = Field(..., description="Total unrealized P&L")
    realized_pnl: float = Field(..., description="Total realized P&L")
    total_pnl: float = Field(..., description="Total P&L")
    return_pct: float = Field(..., description="Return percentage")


class SimulationPosition(BaseModel):
    """Simulation position information."""
    pair: str = Field(..., description="Trading pair")
    side: str = Field(..., description="Position side")
    quantity: float = Field(..., description="Position quantity")
    average_price: float = Field(..., description="Average entry price")
    unrealized_pnl: float = Field(..., description="Unrealized P&L")
    realized_pnl: float = Field(..., description="Realized P&L")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    created_at: datetime = Field(..., description="Position creation time")
    updated_at: datetime = Field(..., description="Last update time")


class SimulationTrade(BaseModel):
    """Simulation trade information."""
    id: str = Field(..., description="Trade ID")
    pair: str = Field(..., description="Trading pair")
    side: str = Field(..., description="Trade side")
    quantity: float = Field(..., description="Trade quantity")
    price: float = Field(..., description="Trade price")
    commission: float = Field(..., description="Commission paid")
    timestamp: datetime = Field(..., description="Trade timestamp")
    order_id: str = Field(..., description="Related order ID")


class SimulationPerformance(BaseModel):
    """Simulation performance metrics."""
    total_return: float = Field(..., description="Total return percentage")
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: float = Field(..., description="Win rate percentage")
    average_win: float = Field(..., description="Average winning trade")
    average_loss: float = Field(..., description="Average losing trade")
    profit_factor: float = Field(..., description="Profit factor")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")


# Dependency functions
def get_simulation_engine() -> SimulationEngine:
    """Get the global simulation engine instance."""
    global _simulation_engine
    if _simulation_engine is None:
        config = SimulationConfig.from_env()
        _simulation_engine = SimulationEngine(config)
    return _simulation_engine


def get_trading_config() -> TradingConfig:
    """Get the global trading configuration."""
    global _trading_config
    if _trading_config is None:
        _trading_config = TradingConfig.from_env()
    return _trading_config


def get_orders_adapter() -> OrdersAdapter:
    """Get the global orders adapter."""
    global _orders_adapter
    if _orders_adapter is None:
        # This would need to be properly initialized with dependencies
        # For now, return None and handle in endpoints
        return None
    return _orders_adapter


# API Endpoints
@router.get("/status", response_model=SimulationStatus)
async def get_simulation_status(
    engine: SimulationEngine = Depends(get_simulation_engine),
    config: TradingConfig = Depends(get_trading_config),
    _: bool = Depends(require_read_access)
) -> SimulationStatus:
    """Get simulation engine status."""
    status_data = engine.get_status()
    
    return SimulationStatus(
        running=status_data["running"],
        mode=config.get_effective_mode(),
        portfolio_value=status_data["portfolio_value"],
        positions_count=status_data["positions_count"],
        orders_count=status_data["orders_count"],
        stats=status_data["stats"]
    )


@router.get("/portfolio", response_model=SimulationPortfolio)
async def get_simulation_portfolio(
    engine: SimulationEngine = Depends(get_simulation_engine),
    _: bool = Depends(require_read_access)
) -> SimulationPortfolio:
    """Get current simulation portfolio."""
    snapshots = engine.get_snapshots()
    if not snapshots:
        # Return empty portfolio if no snapshots
        return SimulationPortfolio(
            total_value=0.0,
            cash=0.0,
            positions_value=0.0,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            total_pnl=0.0,
            return_pct=0.0
        )
    
    latest = snapshots[-1]
    return SimulationPortfolio(
        total_value=float(latest.total_value),
        cash=float(latest.cash),
        positions_value=float(latest.positions_value),
        unrealized_pnl=float(latest.unrealized_pnl),
        realized_pnl=float(latest.realized_pnl),
        total_pnl=float(latest.total_pnl),
        return_pct=float(latest.return_pct)
    )


@router.get("/positions", response_model=List[SimulationPosition])
async def get_simulation_positions(
    engine: SimulationEngine = Depends(get_simulation_engine),
    _: bool = Depends(require_read_access)
) -> List[SimulationPosition]:
    """Get all simulation positions."""
    positions = engine.get_positions()
    
    return [
        SimulationPosition(
            pair=pos.pair,
            side=pos.side.value,
            quantity=float(pos.quantity),
            average_price=float(pos.average_price),
            unrealized_pnl=float(pos.unrealized_pnl),
            realized_pnl=float(pos.realized_pnl),
            stop_loss=float(pos.stop_loss) if pos.stop_loss else None,
            take_profit=float(pos.take_profit) if pos.take_profit else None,
            created_at=pos.created_at,
            updated_at=pos.updated_at
        )
        for pos in positions
    ]


@router.get("/trades", response_model=PaginatedResponse)
async def get_simulation_trades(
    page: int = 1,
    size: int = 50,
    engine: SimulationEngine = Depends(get_simulation_engine),
    _: bool = Depends(require_read_access)
) -> PaginatedResponse:
    """Get simulation trades with pagination."""
    trades = engine.get_trades()
    
    # Sort by timestamp (newest first)
    trades.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply pagination
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    total = len(trades)
    items = trades[start_idx:end_idx]
    pages = (total + size - 1) // size
    
    # Convert to API models
    trade_models = [
        SimulationTrade(
            id=trade.id,
            pair=trade.pair,
            side=trade.side.value,
            quantity=float(trade.quantity),
            price=float(trade.price),
            commission=float(trade.commission),
            timestamp=trade.timestamp,
            order_id=trade.order_id
        )
        for trade in items
    ]
    
    return PaginatedResponse(
        items=trade_models,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/reset", response_model=APIResponse)
async def reset_simulation(
    engine: SimulationEngine = Depends(get_simulation_engine),
    _: bool = Depends(require_read_access)
) -> APIResponse:
    """Reset simulation to initial state."""
    try:
        await engine.reset()
        return APIResponse(
            success=True,
            message="Simulation reset successfully"
        )
    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset simulation: {str(e)}"
        )


@router.get("/performance", response_model=SimulationPerformance)
async def get_simulation_performance(
    engine: SimulationEngine = Depends(get_simulation_engine),
    _: bool = Depends(require_read_access)
) -> SimulationPerformance:
    """Get simulation performance metrics."""
    trades = engine.get_trades()
    snapshots = engine.get_snapshots()
    
    if not trades:
        return SimulationPerformance(
            total_return=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            average_win=0.0,
            average_loss=0.0,
            profit_factor=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0
        )
    
    # Calculate basic metrics
    total_trades = len(trades)
    winning_trades = sum(1 for trade in trades if trade.commission < 0)  # Simplified logic
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
    
    # Calculate total return
    total_return = 0.0
    if snapshots:
        initial_value = float(engine.portfolio.initial_capital)
        current_value = float(snapshots[-1].total_value)
        total_return = ((current_value - initial_value) / initial_value * 100) if initial_value > 0 else 0.0
    
    # Simplified performance calculation
    # In a real implementation, this would be more sophisticated
    return SimulationPerformance(
        total_return=total_return,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        average_win=0.0,  # Would need more sophisticated calculation
        average_loss=0.0,  # Would need more sophisticated calculation
        profit_factor=0.0,  # Would need more sophisticated calculation
        max_drawdown=0.0,  # Would need more sophisticated calculation
        sharpe_ratio=0.0   # Would need more sophisticated calculation
    )


@router.post("/start", response_model=APIResponse)
async def start_simulation(
    engine: SimulationEngine = Depends(get_simulation_engine),
    _: bool = Depends(require_read_access)
) -> APIResponse:
    """Start the simulation engine."""
    try:
        await engine.start()
        return APIResponse(
            success=True,
            message="Simulation engine started successfully"
        )
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start simulation: {str(e)}"
        )


@router.post("/stop", response_model=APIResponse)
async def stop_simulation(
    engine: SimulationEngine = Depends(get_simulation_engine),
    _: bool = Depends(require_read_access)
) -> APIResponse:
    """Stop the simulation engine."""
    try:
        await engine.stop()
        return APIResponse(
            success=True,
            message="Simulation engine stopped successfully"
        )
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop simulation: {str(e)}"
        )


# Admin endpoints for trading approval
@router.post("/admin/trading/approve", response_model=APIResponse)
async def approve_live_trading(
    config: TradingConfig = Depends(get_trading_config),
    _: bool = Depends(require_read_access)
) -> APIResponse:
    """Approve live trading."""
    try:
        config.approve_live_trading()
        return APIResponse(
            success=True,
            message="Live trading approved"
        )
    except Exception as e:
        logger.error(f"Error approving live trading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve live trading: {str(e)}"
        )


@router.post("/admin/trading/revoke", response_model=APIResponse)
async def revoke_live_trading(
    config: TradingConfig = Depends(get_trading_config),
    _: bool = Depends(require_read_access)
) -> APIResponse:
    """Revoke live trading approval."""
    try:
        config.revoke_live_trading()
        return APIResponse(
            success=True,
            message="Live trading approval revoked"
        )
    except Exception as e:
        logger.error(f"Error revoking live trading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke live trading: {str(e)}"
        )
