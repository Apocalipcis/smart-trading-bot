"""Simulation portfolio management."""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from ..orders.types import Order, OrderSide, OrderStatus

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Simulation position."""
    pair: str
    side: OrderSide
    quantity: Decimal
    average_price: Decimal
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_pnl(self, current_price: Decimal) -> None:
        """Update unrealized P&L based on current price."""
        if self.side == OrderSide.BUY:
            self.unrealized_pnl = (current_price - self.average_price) * self.quantity
        else:  # SELL (short)
            self.unrealized_pnl = (self.average_price - current_price) * self.quantity
        
        self.updated_at = datetime.now(timezone.utc)
    
    def get_total_pnl(self) -> Decimal:
        """Get total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl


@dataclass
class Trade:
    """Simulation trade."""
    id: str
    pair: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal
    timestamp: datetime
    order_id: str
    position_id: Optional[str] = None


class PortfolioSnapshot(BaseModel):
    """Portfolio snapshot for tracking performance."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_value: Decimal = Field(..., description="Total portfolio value")
    cash: Decimal = Field(..., description="Available cash")
    positions_value: Decimal = Field(..., description="Value of all positions")
    unrealized_pnl: Decimal = Field(..., description="Total unrealized P&L")
    realized_pnl: Decimal = Field(..., description="Total realized P&L")
    total_pnl: Decimal = Field(..., description="Total P&L")
    return_pct: Decimal = Field(..., description="Return percentage")


class SimulationPortfolio:
    """Manages simulation portfolio including positions, cash, and P&L."""
    
    def __init__(self, initial_capital: Decimal, commission: Decimal = Decimal("0.001")):
        self.initial_capital = initial_capital
        self.commission = commission
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.snapshots: List[PortfolioSnapshot] = []
        self._lock = asyncio.Lock()
        
        # Create initial snapshot
        self._create_snapshot()
    
    async def submit_order(self, order: Order) -> bool:
        """Submit an order to the portfolio."""
        async with self._lock:
            try:
                if order.order_type.value == "market":
                    return await self._execute_market_order(order)
                elif order.order_type.value == "limit":
                    return await self._queue_limit_order(order)
                else:
                    logger.warning(f"Unsupported order type: {order.order_type}")
                    return False
            except Exception as e:
                logger.error(f"Error submitting order: {e}")
                return False
    
    async def _execute_market_order(self, order: Order) -> bool:
        """Execute a market order immediately."""
        # Calculate execution price with slippage
        execution_price = self._calculate_execution_price(order)
        
        # Calculate commission
        commission_amount = execution_price * order.quantity * self.commission
        
        # Check if we have enough cash
        total_cost = execution_price * order.quantity + commission_amount
        
        if order.side == OrderSide.BUY and total_cost > self.cash:
            logger.warning(f"Insufficient cash for buy order: {total_cost} > {self.cash}")
            return False
        
        # Execute the trade
        trade = Trade(
            id=f"SIM-{order.id}",
            pair=order.pair,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            commission=commission_amount,
            timestamp=datetime.now(timezone.utc),
            order_id=order.id
        )
        
        self.trades.append(trade)
        
        # Update cash
        if order.side == OrderSide.BUY:
            self.cash -= total_cost
        else:  # SELL
            self.cash += (execution_price * order.quantity - commission_amount)
        
        # Update position
        await self._update_position(order.pair, order.side, order.quantity, execution_price)
        
        # Update order status
        order.update_status(OrderStatus.FILLED, 
                          filled_quantity=order.quantity,
                          average_price=execution_price,
                          commission=commission_amount,
                          filled_at=datetime.now(timezone.utc))
        
        logger.info(f"Executed market order: {order.side} {order.quantity} {order.pair} @ {execution_price}")
        return True
    
    async def _queue_limit_order(self, order: Order) -> bool:
        """Queue a limit order for later execution."""
        # For now, just mark as submitted
        # In a full implementation, this would be stored in a pending orders list
        order.update_status(OrderStatus.SUBMITTED)
        logger.info(f"Queued limit order: {order.side} {order.quantity} {order.pair} @ {order.price}")
        return True
    
    def _calculate_execution_price(self, order: Order) -> Decimal:
        """Calculate execution price with slippage."""
        # This is a simplified implementation
        # In a real implementation, this would use actual bid/ask prices
        base_price = Decimal("50000")  # Placeholder - should come from price feed
        
        if order.side == OrderSide.BUY:
            # Buy at ask price (higher)
            return base_price * (Decimal("1") + self.commission)
        else:
            # Sell at bid price (lower)
            return base_price * (Decimal("1") - self.commission)
    
    async def _update_position(self, pair: str, side: OrderSide, quantity: Decimal, price: Decimal) -> None:
        """Update position after trade execution."""
        position_key = f"{pair}_{side.value}"
        
        if position_key in self.positions:
            # Update existing position
            position = self.positions[position_key]
            total_quantity = position.quantity + quantity
            total_value = (position.quantity * position.average_price) + (quantity * price)
            position.average_price = total_value / total_quantity
            position.quantity = total_quantity
            position.updated_at = datetime.now(timezone.utc)
        else:
            # Create new position
            self.positions[position_key] = Position(
                pair=pair,
                side=side,
                quantity=quantity,
                average_price=price
            )
    
    async def update_prices(self, price_data: Dict[str, Decimal]) -> None:
        """Update position P&L based on current prices."""
        async with self._lock:
            for position_key, position in self.positions.items():
                pair = position.pair
                if pair in price_data:
                    current_price = price_data[pair]
                    position.update_pnl(current_price)
            
            # Create snapshot
            self._create_snapshot()
    
    def _create_snapshot(self) -> None:
        """Create a portfolio snapshot."""
        positions_value = sum(
            pos.quantity * pos.average_price for pos in self.positions.values()
        )
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        total_pnl = unrealized_pnl + realized_pnl
        total_value = self.cash + positions_value
        
        # Calculate return percentage
        if self.initial_capital > 0:
            return_pct = ((total_value - self.initial_capital) / self.initial_capital) * Decimal("100")
        else:
            return_pct = Decimal("0")
        
        snapshot = PortfolioSnapshot(
            total_value=total_value,
            cash=self.cash,
            positions_value=positions_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            total_pnl=total_pnl,
            return_pct=return_pct
        )
        
        self.snapshots.append(snapshot)
        
        # Keep only last 1000 snapshots
        if len(self.snapshots) > 1000:
            self.snapshots = self.snapshots[-1000:]
    
    def get_positions(self) -> List[Position]:
        """Get all current positions."""
        return list(self.positions.values())
    
    def get_position(self, pair: str, side: OrderSide) -> Optional[Position]:
        """Get specific position."""
        position_key = f"{pair}_{side.value}"
        return self.positions.get(position_key)
    
    def get_trades(self) -> List[Trade]:
        """Get all trades."""
        return self.trades.copy()
    
    def get_snapshots(self) -> List[PortfolioSnapshot]:
        """Get all snapshots."""
        return self.snapshots.copy()
    
    def get_current_value(self) -> Decimal:
        """Get current portfolio value."""
        if self.snapshots:
            return self.snapshots[-1].total_value
        return self.initial_capital
    
    def reset(self) -> None:
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions.clear()
        self.trades.clear()
        self.snapshots.clear()
        self._create_snapshot()
        logger.info("Portfolio reset to initial state")
