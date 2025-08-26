# Simulation Engine Implementation

This document describes the implementation of the SimulationEngine with dual mode support for the Smart Trading Bot.

## Overview

The SimulationEngine provides a complete trading simulation environment that can operate in two modes:
- **Simulation Mode**: Paper trading with realistic market conditions
- **Live Mode**: Real trading with exchange integration (requires approval)

## Architecture

### Core Components

1. **SimulationEngine** (`src/simulation/engine.py`)
   - Main simulation engine that processes orders and manages portfolio
   - Handles price updates and order matching
   - Manages background tasks for tick processing and strategy evaluation

2. **SimulationPortfolio** (`src/simulation/portfolio.py`)
   - Tracks positions, cash, and P&L
   - Manages trade execution and position updates
   - Creates portfolio snapshots for performance tracking

3. **SimulationConfig** (`src/simulation/config.py`)
   - Configuration management for simulation parameters
   - Environment variable integration
   - Mode switching logic

4. **OrdersAdapter** (`src/orders/adapters.py`)
   - Abstract interface for order operations
   - SimulationOrdersAdapter for simulation mode
   - BinanceOrdersAdapter for live trading (placeholder)

5. **SimulationStorage** (`src/storage/simulation.py`)
   - Database schema for simulation data
   - Separate tables for simulation vs live data
   - Complete data isolation

### Key Features

- **Complete Isolation**: Simulation and live data are completely separated
- **Real-time Simulation**: Uses actual WebSocket price feeds for realistic simulation
- **Portfolio Management**: Full P&L tracking and position management
- **Order Processing**: Market and limit order support with slippage and commission
- **Performance Tracking**: Portfolio snapshots and performance metrics
- **Approval Gate**: Live trading requires explicit approval

## Configuration

### Environment Variables

```env
# Trading mode: simulation or live
TRADING_MODE=simulation

# Live trading approval
TRADING_APPROVED=false

# Simulation settings
SIMULATION_INITIAL_CAPITAL=10000.0
SIMULATION_COMMISSION=0.001
SIMULATION_SLIPPAGE=0.0001
SIMULATION_TICK_INTERVAL=5.0
SIMULATION_STRATEGY_INTERVAL=60.0

# Risk management
MAX_OPEN_POSITIONS=5
MAX_RISK_PER_TRADE=2.0
MIN_RISK_REWARD_RATIO=3.0
```

### Mode Logic

1. **Simulation Mode** (default):
   - No API keys required
   - Uses SimulationEngine for all operations
   - Data stored in simulation-specific tables
   - Safe for testing and development

2. **Live Mode**:
   - Requires `TRADING_APPROVED=true`
   - Requires valid API keys
   - Uses real exchange integration
   - Data stored in live-specific tables

## API Endpoints

### Simulation Endpoints

- `GET /api/v1/simulation/status` - Get simulation engine status
- `GET /api/v1/simulation/portfolio` - Get current portfolio
- `GET /api/v1/simulation/positions` - Get open positions
- `GET /api/v1/simulation/trades` - Get trade history
- `GET /api/v1/simulation/performance` - Get performance metrics
- `POST /api/v1/simulation/reset` - Reset simulation
- `POST /api/v1/simulation/start` - Start simulation engine
- `POST /api/v1/simulation/stop` - Stop simulation engine

### Admin Endpoints

- `POST /api/v1/simulation/admin/trading/approve` - Approve live trading
- `POST /api/v1/simulation/admin/trading/revoke` - Revoke live trading

## Database Schema

### Simulation Tables

- `orders_sim` - Simulation orders with SIM- prefix
- `trades_sim` - Simulation trades
- `positions_sim` - Current simulation positions
- `equity_snapshots_sim` - Portfolio value over time
- `simulation_config` - Simulation settings

### Data Isolation

- All simulation data uses `_sim` suffix
- Order IDs use `SIM-` prefix
- No cross-contamination between modes
- Separate indexes and constraints

## Usage Examples

### Basic Simulation

```python
from src.simulation.config import SimulationConfig
from src.simulation.engine import SimulationEngine
from src.orders.types import Order, OrderSide, OrderType

# Create configuration
config = SimulationConfig(
    initial_capital=Decimal("10000.0"),
    commission=Decimal("0.001")
)

# Create and start engine
engine = SimulationEngine(config)
await engine.start()

# Submit an order
order = Order(
    pair="BTCUSDT",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=Decimal("0.001")
)

result = await engine.submit_order(order)
print(f"Order submitted: {result.success}")
```

### Using OrdersAdapter

```python
from src.orders.adapters import OrdersAdapterFactory

# Create adapter based on mode
adapter = await OrdersAdapterFactory.create_adapter(
    mode="simulation",
    simulation_engine=engine
)

# Connect and use
await adapter.connect()
result = await adapter.submit_order(order)
```

## Testing

### Running Tests

```bash
# Run simulation tests
pytest tests/test_simulation.py -v

# Run with coverage
pytest tests/test_simulation.py --cov=src.simulation --cov-report=html
```

### Demo Script

```bash
# Run the demo
python examples/simulation_demo.py
```

## Integration Points

### WebSocket Integration

The simulation engine can integrate with the existing WebSocket stream manager:

```python
# Add price callback to simulation engine
def price_callback(price_data):
    for pair, data in price_data.items():
        asyncio.create_task(engine.update_price(
            pair=pair,
            bid=data.bid,
            ask=data.ask,
            last=data.last
        ))

# Register callback with WebSocket manager
ws_manager.add_price_callback(price_callback)
```

### Strategy Integration

Strategies can use the same OrdersAdapter interface regardless of mode:

```python
class MyStrategy:
    def __init__(self, orders_adapter: OrdersAdapter):
        self.adapter = orders_adapter
    
    async def execute_signal(self, signal):
        order = Order(
            pair=signal.pair,
            side=signal.side,
            order_type=OrderType.MARKET,
            quantity=signal.quantity
        )
        
        result = await self.adapter.submit_order(order)
        return result
```

## Performance Considerations

### Memory Usage

- Portfolio snapshots are limited to 1000 entries
- Price data is cached in memory
- Orders and trades are stored in memory during runtime

### Database Performance

- Separate tables for simulation vs live data
- Indexes on frequently queried columns
- WAL mode for better concurrency

### Scalability

- Asynchronous operations throughout
- Background tasks for non-critical operations
- Configurable tick intervals

## Security

### Live Trading Protection

- Explicit approval required for live trading
- API key validation
- Mode isolation prevents accidental live trades
- Audit trail for all operations

### Data Protection

- Separate database tables for simulation vs live
- No cross-contamination between modes
- Secure credential handling

## Future Enhancements

### Planned Features

1. **Advanced Order Types**
   - Stop orders
   - Trailing stops
   - OCO orders

2. **Risk Management**
   - Position sizing algorithms
   - Dynamic stop losses
   - Portfolio heat maps

3. **Performance Analytics**
   - Sharpe ratio calculation
   - Maximum drawdown analysis
   - Risk-adjusted returns

4. **Real-time Monitoring**
   - WebSocket dashboard updates
   - Real-time P&L streaming
   - Alert system

### Integration Opportunities

1. **Multiple Exchanges**
   - Support for other exchanges
   - Multi-exchange arbitrage simulation

2. **Advanced Strategies**
   - Machine learning integration
   - Multi-timeframe analysis
   - Portfolio optimization

3. **Reporting**
   - PDF report generation
   - Email notifications
   - Telegram integration

## Troubleshooting

### Common Issues

1. **Simulation Engine Not Starting**
   - Check configuration values
   - Verify database connection
   - Check for conflicting processes

2. **Orders Not Filling**
   - Verify price data is being updated
   - Check order validation
   - Review commission and slippage settings

3. **Performance Issues**
   - Adjust tick intervals
   - Monitor memory usage
   - Check database performance

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('src.simulation').setLevel(logging.DEBUG)
```

## Support

For issues and questions:

1. Check the test suite for examples
2. Review the demo script
3. Check the API documentation
4. Review the logs for error messages

## Changelog

### v1.0.0
- Initial simulation engine implementation
- Basic order processing and portfolio management
- API endpoints for simulation control
- Database schema for simulation data
- Complete mode isolation
- Order adapter interface
- Comprehensive test suite
