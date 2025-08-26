"""Tests for simulation engine."""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timezone

from src.simulation.config import SimulationConfig
from src.simulation.engine import SimulationEngine
from src.simulation.portfolio import Position, Trade
from src.orders.types import Order, OrderSide, OrderType, OrderStatus


class TestSimulationConfig:
    """Test simulation configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SimulationConfig()
        
        assert config.trading_mode == "simulation"
        assert config.trading_approved is False
        assert config.initial_capital == Decimal("10000.0")
        assert config.commission == Decimal("0.001")
        assert config.slippage == Decimal("0.0001")
    
    def test_is_simulation_mode(self):
        """Test simulation mode detection."""
        config = SimulationConfig()
        assert config.is_simulation_mode() is True
        
        config.trading_mode = "live"
        config.trading_approved = False
        assert config.is_simulation_mode() is True
        
        config.trading_approved = True
        assert config.is_simulation_mode() is False
    
    def test_is_live_mode(self):
        """Test live mode detection."""
        config = SimulationConfig()
        assert config.is_live_mode() is False
        
        config.trading_mode = "live"
        config.trading_approved = True
        assert config.is_live_mode() is True


class TestSimulationEngine:
    """Test simulation engine."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SimulationConfig(
            initial_capital=Decimal("10000.0"),
            commission=Decimal("0.001"),
            slippage=Decimal("0.0001")
        )
    
    @pytest.fixture
    def engine(self, config):
        """Create test simulation engine."""
        return SimulationEngine(config)
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.config is not None
        assert engine.portfolio is not None
        assert engine._running is False
        assert len(engine.orders) == 0
        assert len(engine.price_data) == 0
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self, engine):
        """Test engine start and stop."""
        # Start engine
        await engine.start()
        assert engine._running is True
        
        # Stop engine
        await engine.stop()
        assert engine._running is False
    
    @pytest.mark.asyncio
    async def test_submit_market_order(self, engine):
        """Test submitting a market order."""
        await engine.start()
        
        # Create a market order
        order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        # Submit order
        result = await engine.submit_order(order)
        
        assert result.success is True
        assert result.order_id.startswith("SIM-")
        assert order.status == OrderStatus.FILLED
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_portfolio_value(self, engine):
        """Test portfolio value calculation."""
        await engine.start()
        
        # Initial value should match initial capital
        initial_value = engine.get_portfolio_value()
        assert initial_value == Decimal("10000.0")
        
        # Submit a buy order
        order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        await engine.submit_order(order)
        
        # Value should be less due to commission
        new_value = engine.get_portfolio_value()
        assert new_value < initial_value
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_price_update(self, engine):
        """Test price update functionality."""
        await engine.start()
        
        # Update price
        await engine.update_price(
            pair="BTCUSDT",
            bid=Decimal("50000"),
            ask=Decimal("50001"),
            last=Decimal("50000.5")
        )
        
        # Check price data
        price_data = engine.get_price_data("BTCUSDT")
        assert price_data is not None
        assert price_data.bid == Decimal("50000")
        assert price_data.ask == Decimal("50001")
        assert price_data.last == Decimal("50000.5")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_engine_reset(self, engine):
        """Test engine reset functionality."""
        await engine.start()
        
        # Submit an order to create some state
        order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        await engine.submit_order(order)
        
        # Verify state exists
        assert len(engine.orders) > 0
        assert engine.get_portfolio_value() < Decimal("10000.0")
        
        # Reset engine
        await engine.reset()
        
        # Verify state is reset
        assert len(engine.orders) == 0
        assert engine.get_portfolio_value() == Decimal("10000.0")
        
        await engine.stop()


class TestSimulationPortfolio:
    """Test simulation portfolio."""
    
    @pytest.fixture
    def portfolio(self):
        """Create test portfolio."""
        from src.simulation.portfolio import SimulationPortfolio
        return SimulationPortfolio(
            initial_capital=Decimal("10000.0"),
            commission=Decimal("0.001")
        )
    
    @pytest.mark.asyncio
    async def test_portfolio_initialization(self, portfolio):
        """Test portfolio initialization."""
        assert portfolio.initial_capital == Decimal("10000.0")
        assert portfolio.cash == Decimal("10000.0")
        assert len(portfolio.positions) == 0
        assert len(portfolio.trades) == 0
        assert len(portfolio.snapshots) == 1  # Initial snapshot
    
    @pytest.mark.asyncio
    async def test_market_order_execution(self, portfolio):
        """Test market order execution."""
        order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        success = await portfolio.submit_order(order)
        assert success is True
        
        # Check that order was filled
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == Decimal("0.001")
        assert order.average_price is not None
        assert order.commission > 0
        
        # Check that trade was created
        assert len(portfolio.trades) == 1
        trade = portfolio.trades[0]
        assert trade.pair == "BTCUSDT"
        assert trade.side == OrderSide.BUY
        assert trade.quantity == Decimal("0.001")
    
    @pytest.mark.asyncio
    async def test_position_creation(self, portfolio):
        """Test position creation."""
        order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        await portfolio.submit_order(order)
        
        # Check that position was created
        position = portfolio.get_position("BTCUSDT", OrderSide.BUY)
        assert position is not None
        assert position.pair == "BTCUSDT"
        assert position.side == OrderSide.BUY
        assert position.quantity == Decimal("0.001")
    
    @pytest.mark.asyncio
    async def test_portfolio_reset(self, portfolio):
        """Test portfolio reset."""
        # Create some state
        order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        await portfolio.submit_order(order)
        
        # Verify state exists
        assert len(portfolio.trades) > 0
        assert len(portfolio.positions) > 0
        assert portfolio.cash < Decimal("10000.0")
        
        # Reset portfolio
        portfolio.reset()
        
        # Verify state is reset
        assert len(portfolio.trades) == 0
        assert len(portfolio.positions) == 0
        assert portfolio.cash == Decimal("10000.0")
        assert len(portfolio.snapshots) == 1  # Only initial snapshot


if __name__ == "__main__":
    pytest.main([__file__])
