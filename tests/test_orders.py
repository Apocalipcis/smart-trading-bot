"""Tests for the orders package."""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timezone

from src.orders.sizing import PositionSizer, RiskModel
from src.orders.types import (
    Order, MarketOrder, LimitOrder, StopMarketOrder, 
    StopLimitOrder, TrailingStopOrder, OrderStatus, OrderSide, OrderType
)
from src.orders.queue import OrderQueue, QueuePriority, OrderSubmissionResult
from src.orders.pending import PendingConfirmationStore, ConfirmationAction


class TestPositionSizer:
    """Test position sizing calculations."""
    
    def test_fixed_risk_calculation(self):
        """Test fixed risk position sizing."""
        sizer = PositionSizer(
            account_balance=Decimal('10000'),
            risk_percentage=Decimal('2.0')
        )
        
        result = sizer.calculate_position_size(
            entry_price=Decimal('50000'),
            stop_loss=Decimal('49000'),
            leverage=1
        )
        
        assert result["position_size"] > 0
        assert result["risk_amount"] == Decimal('200')  # 2% of 10000
        assert result["risk_percentage"] == Decimal('2.0')
    
    def test_leverage_calculation(self):
        """Test leverage affects position size."""
        sizer = PositionSizer(
            account_balance=Decimal('10000'),
            risk_percentage=Decimal('2.0')
        )
        
        result_1x = sizer.calculate_position_size(
            entry_price=Decimal('50000'),
            stop_loss=Decimal('49000'),
            leverage=1
        )
        
        result_10x = sizer.calculate_position_size(
            entry_price=Decimal('50000'),
            stop_loss=Decimal('49000'),
            leverage=10
        )
        
        assert result_10x["position_size"] == result_1x["position_size"] * 10
        assert result_10x["leverage"] == 10
    
    def test_short_position_calculation(self):
        """Test short position sizing."""
        sizer = PositionSizer(
            account_balance=Decimal('10000'),
            risk_percentage=Decimal('2.0')
        )
        
        result = sizer.calculate_position_size(
            entry_price=Decimal('50000'),
            stop_loss=Decimal('51000'),  # Higher stop loss for short
            leverage=1
        )
        
        assert result["position_size"] > 0
        assert result["risk_amount"] == Decimal('200')
    
    def test_invalid_inputs(self):
        """Test invalid inputs raise errors."""
        sizer = PositionSizer(
            account_balance=Decimal('10000'),
            risk_percentage=Decimal('2.0')
        )
        
        # Same entry and stop loss
        with pytest.raises(ValueError):
            sizer.calculate_position_size(
                entry_price=Decimal('50000'),
                stop_loss=Decimal('50000'),
                leverage=1
            )
        
        # Invalid leverage
        with pytest.raises(ValueError):
            sizer.calculate_position_size(
                entry_price=Decimal('50000'),
                stop_loss=Decimal('49000'),
                leverage=200  # Too high
            )


class TestOrderTypes:
    """Test order type implementations."""
    
    def test_market_order(self):
        """Test market order creation."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        assert order.order_type == OrderType.MARKET
        assert order.price is None
        assert order.status == OrderStatus.PENDING
    
    def test_limit_order(self):
        """Test limit order creation."""
        order = LimitOrder(
            pair="BTCUSDT",
            side=OrderSide.SELL,
            quantity=Decimal('0.1'),
            price=Decimal('50000')
        )
        
        assert order.order_type == OrderType.LIMIT
        assert order.price == Decimal('50000')
        assert order.time_in_force == "GTC"
    
    def test_stop_market_order(self):
        """Test stop market order creation."""
        order = StopMarketOrder(
            pair="BTCUSDT",
            side=OrderSide.SELL,
            quantity=Decimal('0.1'),
            stop_price=Decimal('45000')
        )
        
        assert order.order_type == OrderType.STOP_MARKET
        assert order.stop_price == Decimal('45000')
        assert order.price is None
    
    def test_stop_limit_order(self):
        """Test stop limit order creation."""
        order = StopLimitOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1'),
            stop_price=Decimal('45000'),
            price=Decimal('45100')
        )
        
        assert order.order_type == OrderType.STOP_LIMIT
        assert order.stop_price == Decimal('45000')
        assert order.price == Decimal('45100')
    
    def test_trailing_stop_order(self):
        """Test trailing stop order creation."""
        order = TrailingStopOrder(
            pair="BTCUSDT",
            side=OrderSide.SELL,
            quantity=Decimal('0.1'),
            stop_price=Decimal('50000'),
            trailing_percent=Decimal('2.0')
        )
        
        assert order.order_type == OrderType.TRAILING_STOP
        assert order.trailing_percent == Decimal('2.0')
    
    def test_order_status_updates(self):
        """Test order status updates."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        assert order.is_active()
        assert not order.is_filled()
        assert not order.is_cancelled()
        
        order.update_status(OrderStatus.FILLED, filled_quantity=Decimal('0.1'))
        
        assert not order.is_active()
        assert order.is_filled()
        assert order.filled_quantity == Decimal('0.1')
    
    def test_trailing_stop_update(self):
        """Test trailing stop price updates."""
        order = TrailingStopOrder(
            pair="BTCUSDT",
            side=OrderSide.SELL,
            quantity=Decimal('0.1'),
            stop_price=Decimal('50000'),
            trailing_percent=Decimal('2.0')
        )
        
        # For SELL orders, when price goes up (52000), trailing stop should move up
        # 2% trailing from 52000 = 52000 * 1.02 = 53040
        updated = order.update_trailing_stop(Decimal('52000'))
        assert updated
        assert order.stop_price > Decimal('50000')
        
        # Price moved in unfavorable direction (down for SELL)
        updated = order.update_trailing_stop(Decimal('48000'))
        assert not updated


class TestOrderQueue:
    """Test order queue functionality."""
    
    @pytest.fixture
    async def queue(self):
        """Create order queue for testing."""
        queue = OrderQueue(max_concurrent_orders=2)
        await queue.start()
        yield queue
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_order_submission(self, queue):
        """Test order submission to queue."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        order_id = await queue.submit_order(order, priority=QueuePriority.HIGH)
        
        assert order_id == order.id
        
        # Check queue stats
        stats = queue.get_queue_stats()
        assert stats["statistics"]["submitted"] == 1
        assert stats["queue_sizes"]["high"] == 1
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, queue):
        """Test duplicate order detection."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        # Submit same order twice
        order_id_1 = await queue.submit_order(order)
        order_id_2 = await queue.submit_order(order)
        
        assert order_id_1 == order_id_2
        
        stats = queue.get_queue_stats()
        assert stats["statistics"]["duplicates"] == 1
    
    @pytest.mark.asyncio
    async def test_order_cancellation(self, queue):
        """Test order cancellation."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        order_id = await queue.submit_order(order)
        
        # Cancel the order
        cancelled = await queue.cancel_order(order_id)
        assert cancelled
        
        # Check order status
        result = await queue.get_order_status(order_id)
        assert result is None  # Order was cancelled before processing


class TestPendingConfirmationStore:
    """Test pending confirmation store."""
    
    @pytest.fixture
    async def store(self):
        """Create pending confirmation store for testing."""
        store = PendingConfirmationStore(default_ttl_seconds=60)
        await store.start()
        yield store
        await store.stop()
    
    @pytest.mark.asyncio
    async def test_add_pending_confirmation(self, store):
        """Test adding pending confirmation."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        order_id = await store.add_pending_confirmation(order, ttl_seconds=300)
        
        assert order_id == order.id
        
        # Check pending confirmation
        pending = await store.get_pending_confirmation(order_id)
        assert pending is not None
        assert pending.order_id == order_id
        assert not pending.is_expired()
    
    @pytest.mark.asyncio
    async def test_confirm_order(self, store):
        """Test order confirmation."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        order_id = await store.add_pending_confirmation(order)
        
        # Confirm the order
        result = await store.confirm_order(
            order_id, 
            action=ConfirmationAction.APPROVE
        )
        
        assert result is not None
        assert result.action == ConfirmationAction.APPROVE
        assert result.order_id == order_id
        
        # Check it's no longer pending
        pending = await store.get_pending_confirmation(order_id)
        assert pending is None
        
        # Check result is stored
        stored_result = await store.get_confirmation_result(order_id)
        assert stored_result is not None
    
    @pytest.mark.asyncio
    async def test_expired_confirmation(self, store):
        """Test expired confirmation handling."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        # Add with very short TTL
        order_id = await store.add_pending_confirmation(order, ttl_seconds=1)
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Try to confirm expired order
        result = await store.confirm_order(
            order_id, 
            action=ConfirmationAction.APPROVE
        )
        
        assert result is None
        
        # Check it was automatically expired
        pending = await store.get_pending_confirmation(order_id)
        assert pending is None
    
    @pytest.mark.asyncio
    async def test_list_pending_confirmations(self, store):
        """Test listing pending confirmations."""
        # Add multiple orders
        orders = []
        for i in range(3):
            order = MarketOrder(
                pair=f"BTCUSDT",
                side=OrderSide.BUY,
                quantity=Decimal('0.1')
            )
            await store.add_pending_confirmation(order)
            orders.append(order)
        
        # List pending confirmations
        pending_list = await store.list_pending_confirmations()
        
        assert len(pending_list) == 3
        
        # Confirm one order
        await store.confirm_order(orders[0].id, ConfirmationAction.APPROVE)
        
        # List again
        pending_list = await store.list_pending_confirmations()
        assert len(pending_list) == 2
    
    @pytest.mark.asyncio
    async def test_store_statistics(self, store):
        """Test store statistics."""
        order = MarketOrder(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal('0.1')
        )
        
        # Add order
        await store.add_pending_confirmation(order)
        
        stats = store.get_store_stats()
        assert stats["pending_count"] == 1
        assert stats["active_count"] == 1
        assert stats["statistics"]["total_added"] == 1
        
        # Confirm order
        await store.confirm_order(order.id, ConfirmationAction.APPROVE)
        
        stats = store.get_store_stats()
        assert stats["pending_count"] == 0
        assert stats["active_count"] == 0
        assert stats["statistics"]["total_confirmed"] == 1
