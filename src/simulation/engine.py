"""Core simulation engine for trading bot."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from ..orders.types import Order, OrderStatus, OrderSide, OrderType
from ..orders.queue import OrderSubmissionResult
from .portfolio import SimulationPortfolio, Position, Trade
from .config import SimulationConfig

logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    """Price data for a trading pair."""
    pair: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    timestamp: datetime
    
    @property
    def mid_price(self) -> Decimal:
        """Get mid price."""
        return (self.bid + self.ask) / Decimal("2")


class SimulationEngine:
    """Core simulation engine for processing orders and managing portfolio."""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.portfolio = SimulationPortfolio(
            initial_capital=config.initial_capital,
            commission=config.commission
        )
        
        # Price management
        self.price_data: Dict[str, PriceData] = {}
        self.price_callbacks: List[Callable[[Dict[str, PriceData]], None]] = []
        
        # Order management
        self.orders: Dict[str, Order] = {}
        self.pending_orders: Dict[str, Order] = {}
        
        # Engine state
        self._running = False
        self._tick_task: Optional[asyncio.Task] = None
        self._strategy_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            "orders_submitted": 0,
            "orders_filled": 0,
            "orders_cancelled": 0,
            "total_volume": Decimal("0"),
            "total_commission": Decimal("0")
        }
    
    async def start(self) -> None:
        """Start the simulation engine."""
        if self._running:
            logger.warning("Simulation engine is already running")
            return
        
        self._running = True
        
        # Start background tasks
        self._tick_task = asyncio.create_task(self._tick_loop())
        self._strategy_task = asyncio.create_task(self._strategy_loop())
        
        logger.info("Simulation engine started")
    
    async def stop(self) -> None:
        """Stop the simulation engine."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel background tasks
        if self._tick_task:
            self._tick_task.cancel()
        if self._strategy_task:
            self._strategy_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(
            self._tick_task, 
            self._strategy_task, 
            return_exceptions=True
        )
        
        logger.info("Simulation engine stopped")
    
    async def submit_order(self, order: Order) -> OrderSubmissionResult:
        """Submit an order to the simulation engine."""
        async with self._lock:
            try:
                # Generate simulation order ID
                sim_order_id = f"SIM-{uuid.uuid4()}"
                order.id = sim_order_id
                
                # Store order
                self.orders[sim_order_id] = order
                
                # Submit to portfolio with current price data
                price_dict = {pair: data.mid_price for pair, data in self.price_data.items()}
                success = await self.portfolio.submit_order(order, price_dict)
                
                if success:
                    self.stats["orders_submitted"] += 1
                    if order.status == OrderStatus.FILLED:
                        self.stats["orders_filled"] += 1
                        self.stats["total_volume"] += order.quantity
                        self.stats["total_commission"] += order.commission
                    
                    return OrderSubmissionResult(
                        success=True,
                        order_id=sim_order_id,
                        status=order.status,
                        submitted_at=datetime.now(timezone.utc)
                    )
                else:
                    return OrderSubmissionResult(
                        success=False,
                        order_id=sim_order_id,
                        status=OrderStatus.REJECTED,
                        error_message="Order submission failed",
                        submitted_at=datetime.now(timezone.utc)
                    )
                    
            except Exception as e:
                logger.error(f"Error submitting order: {e}")
                return OrderSubmissionResult(
                    success=False,
                    order_id=order.id,
                    status=OrderStatus.REJECTED,
                    error_message=str(e),
                    submitted_at=datetime.now(timezone.utc)
                )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        async with self._lock:
            if order_id in self.orders:
                order = self.orders[order_id]
                if order.is_active():
                    order.update_status(OrderStatus.CANCELLED)
                    self.stats["orders_cancelled"] += 1
                    logger.info(f"Cancelled order: {order_id}")
                    return True
            
            return False
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID."""
        return self.orders.get(order_id)
    
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """Get all orders with optional status filter."""
        orders = list(self.orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders
    
    def get_positions(self) -> List[Position]:
        """Get all current positions."""
        return self.portfolio.get_positions()
    
    def get_position(self, pair: str, side: OrderSide) -> Optional[Position]:
        """Get specific position."""
        return self.portfolio.get_position(pair, side)
    
    def get_trades(self) -> List[Trade]:
        """Get all trades."""
        return self.portfolio.get_trades()
    
    def get_portfolio_value(self) -> Decimal:
        """Get current portfolio value."""
        return self.portfolio.get_current_value()
    
    def get_snapshots(self) -> List[Any]:
        """Get portfolio snapshots."""
        return self.portfolio.get_snapshots()
    
    async def update_price(self, pair: str, bid: Decimal, ask: Decimal, last: Decimal) -> None:
        """Update price data for a trading pair."""
        price_data = PriceData(
            pair=pair,
            bid=bid,
            ask=ask,
            last=last,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.price_data[pair] = price_data
        
        # Update portfolio P&L
        price_dict = {pair: price_data.mid_price}
        await self.portfolio.update_prices(price_dict)
        
        # Notify callbacks
        for callback in self.price_callbacks:
            try:
                callback(self.price_data)
            except Exception as e:
                logger.error(f"Error in price callback: {e}")
    
    def add_price_callback(self, callback: Callable[[Dict[str, PriceData]], None]) -> None:
        """Add a callback for price updates."""
        self.price_callbacks.append(callback)
    
    def get_price_data(self, pair: str) -> Optional[PriceData]:
        """Get price data for a trading pair."""
        return self.price_data.get(pair)
    
    def get_all_prices(self) -> Dict[str, PriceData]:
        """Get all price data."""
        return self.price_data.copy()
    
    async def reset(self) -> None:
        """Reset the simulation engine."""
        async with self._lock:
            # Reset portfolio
            self.portfolio.reset()
            
            # Clear orders
            self.orders.clear()
            self.pending_orders.clear()
            
            # Reset statistics
            self.stats = {
                "orders_submitted": 0,
                "orders_filled": 0,
                "orders_cancelled": 0,
                "total_volume": Decimal("0"),
                "total_commission": Decimal("0")
            }
            
            logger.info("Simulation engine reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get simulation engine status."""
        return {
            "running": self._running,
            "config": self.config.dict(),
            "portfolio_value": float(self.get_portfolio_value()),
            "positions_count": len(self.get_positions()),
            "orders_count": len(self.orders),
            "pending_orders_count": len(self.pending_orders),
            "stats": self.stats,
            "price_pairs": list(self.price_data.keys())
        }
    
    async def _tick_loop(self) -> None:
        """Main tick loop for processing orders and updates."""
        while self._running:
            try:
                # Process pending orders
                await self._process_pending_orders()
                
                # Check stop losses and take profits
                await self._check_risk_management()
                
                # Wait for next tick
                await asyncio.sleep(self.config.tick_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in tick loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _strategy_loop(self) -> None:
        """Strategy evaluation loop."""
        while self._running:
            try:
                # This is where strategy signals would be processed
                # For now, just wait
                await asyncio.sleep(self.config.strategy_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in strategy loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _process_pending_orders(self) -> None:
        """Process pending limit orders."""
        # This is a simplified implementation
        # In a full implementation, this would check if limit orders should be filled
        pass
    
    async def _check_risk_management(self) -> None:
        """Check and execute stop losses and take profits."""
        # This is a simplified implementation
        # In a full implementation, this would check SL/TP levels
        pass
