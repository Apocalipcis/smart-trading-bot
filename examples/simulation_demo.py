"""Demo script for the simulation engine."""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timezone

from src.simulation.config import SimulationConfig
from src.simulation.engine import SimulationEngine
from src.orders.types import Order, OrderSide, OrderType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_simulation_engine():
    """Demonstrate the simulation engine functionality."""
    
    print("🚀 Starting Simulation Engine Demo")
    print("=" * 50)
    
    # Create simulation configuration
    config = SimulationConfig(
        initial_capital=Decimal("10000.0"),
        commission=Decimal("0.001"),
        slippage=Decimal("0.0001"),
        tick_interval=1.0,  # Fast ticks for demo
        strategy_interval=5.0
    )
    
    print(f"📊 Initial Capital: ${config.initial_capital}")
    print(f"💸 Commission Rate: {config.commission * 100}%")
    print(f"📈 Slippage Rate: {config.slippage * 100}%")
    print()
    
    # Create and start simulation engine
    engine = SimulationEngine(config)
    await engine.start()
    
    print("✅ Simulation engine started")
    print()
    
    # Update some prices
    print("📊 Updating price data...")
    await engine.update_price("BTCUSDT", Decimal("50000"), Decimal("50001"), Decimal("50000.5"))
    await engine.update_price("ETHUSDT", Decimal("3000"), Decimal("3001"), Decimal("3000.5"))
    
    print(f"💰 BTCUSDT: ${engine.get_price_data('BTCUSDT').mid_price}")
    print(f"💰 ETHUSDT: ${engine.get_price_data('ETHUSDT').mid_price}")
    print()
    
    # Show initial portfolio
    initial_value = engine.get_portfolio_value()
    print(f"💼 Initial Portfolio Value: ${initial_value}")
    print()
    
    # Submit some orders
    print("📝 Submitting orders...")
    
    # Buy BTC
    btc_order = Order(
        pair="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.001")
    )
    
    result = await engine.submit_order(btc_order)
    print(f"📈 BTC Buy Order: {'✅ Success' if result.success else '❌ Failed'}")
    if result.success:
        print(f"   Order ID: {result.order_id}")
        print(f"   Status: {result.status}")
        print(f"   Fill Price: ${btc_order.average_price}")
        print(f"   Commission: ${btc_order.commission}")
    
    print()
    
    # Buy ETH
    eth_order = Order(
        pair="ETHUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.01")
    )
    
    result = await engine.submit_order(eth_order)
    print(f"📈 ETH Buy Order: {'✅ Success' if result.success else '❌ Failed'}")
    if result.success:
        print(f"   Order ID: {result.order_id}")
        print(f"   Status: {result.status}")
        print(f"   Fill Price: ${eth_order.average_price}")
        print(f"   Commission: ${eth_order.commission}")
    
    print()
    
    # Show updated portfolio
    current_value = engine.get_portfolio_value()
    print(f"💼 Current Portfolio Value: ${current_value}")
    print(f"📊 Portfolio Change: ${current_value - initial_value}")
    print()
    
    # Show positions
    positions = engine.get_positions()
    print(f"📋 Open Positions ({len(positions)}):")
    for pos in positions:
        print(f"   {pos.pair} {pos.side.value.upper()}: {pos.quantity} @ ${pos.average_price}")
        print(f"     Unrealized P&L: ${pos.unrealized_pnl}")
    
    print()
    
    # Show trades
    trades = engine.get_trades()
    print(f"💱 Recent Trades ({len(trades)}):")
    for trade in trades:
        print(f"   {trade.timestamp.strftime('%H:%M:%S')} {trade.pair} {trade.side.value.upper()}: {trade.quantity} @ ${trade.price}")
    
    print()
    
    # Update prices to see P&L changes
    print("📊 Updating prices...")
    await engine.update_price("BTCUSDT", Decimal("51000"), Decimal("51001"), Decimal("51000.5"))
    await engine.update_price("ETHUSDT", Decimal("3100"), Decimal("3101"), Decimal("3100.5"))
    
    print(f"💰 BTCUSDT: ${engine.get_price_data('BTCUSDT').mid_price}")
    print(f"💰 ETHUSDT: ${engine.get_price_data('ETHUSDT').mid_price}")
    print()
    
    # Show updated positions with P&L
    positions = engine.get_positions()
    print(f"📋 Updated Positions:")
    for pos in positions:
        print(f"   {pos.pair} {pos.side.value.upper()}: {pos.quantity} @ ${pos.average_price}")
        print(f"     Unrealized P&L: ${pos.unrealized_pnl}")
    
    print()
    
    # Show final portfolio
    final_value = engine.get_portfolio_value()
    print(f"💼 Final Portfolio Value: ${final_value}")
    print(f"📊 Total Return: ${final_value - initial_value}")
    print(f"📈 Return %: {((final_value - initial_value) / initial_value * 100):.2f}%")
    print()
    
    # Show engine statistics
    stats = engine.get_status()
    print(f"📊 Engine Statistics:")
    print(f"   Orders Submitted: {stats['stats']['orders_submitted']}")
    print(f"   Orders Filled: {stats['stats']['orders_filled']}")
    print(f"   Total Volume: {stats['stats']['total_volume']}")
    print(f"   Total Commission: ${stats['stats']['total_commission']}")
    print()
    
    # Stop the engine
    await engine.stop()
    print("🛑 Simulation engine stopped")
    print()
    print("🎉 Demo completed!")


async def demo_portfolio_reset():
    """Demonstrate portfolio reset functionality."""
    
    print("\n🔄 Portfolio Reset Demo")
    print("=" * 30)
    
    # Create simulation engine
    config = SimulationConfig(initial_capital=Decimal("10000.0"))
    engine = SimulationEngine(config)
    await engine.start()
    
    # Submit some orders
    order = Order(
        pair="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.001")
    )
    
    await engine.submit_order(order)
    
    print(f"📊 Before Reset:")
    print(f"   Portfolio Value: ${engine.get_portfolio_value()}")
    print(f"   Orders Count: {len(engine.get_orders())}")
    print(f"   Positions Count: {len(engine.get_positions())}")
    print(f"   Trades Count: {len(engine.get_trades())}")
    
    # Reset portfolio
    await engine.reset()
    
    print(f"📊 After Reset:")
    print(f"   Portfolio Value: ${engine.get_portfolio_value()}")
    print(f"   Orders Count: {len(engine.get_orders())}")
    print(f"   Positions Count: {len(engine.get_positions())}")
    print(f"   Trades Count: {len(engine.get_trades())}")
    
    await engine.stop()
    print("✅ Reset demo completed!")


if __name__ == "__main__":
    # Run the demos
    asyncio.run(demo_simulation_engine())
    asyncio.run(demo_portfolio_reset())
