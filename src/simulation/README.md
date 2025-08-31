# Simulation Engine Package

A comprehensive paper trading environment for the Smart Trading Bot that provides risk-free strategy testing with real-time data feeds, complete portfolio management, and realistic order simulation.

## 🚀 Quick Start

### What This Package Does
- **Paper Trading Environment**: Risk-free strategy testing with real-time data
- **Portfolio Management**: Complete P&L tracking and position management
- **Order Simulation**: Market orders with slippage and commission modeling
- **Performance Analytics**: Comprehensive trading metrics and reporting
- **Data Isolation**: Separate simulation database for complete isolation

### Run the Demo (5 minutes)
```bash
# From project root
cd examples
python simulation_demo.py
```

You should see:
- Simulation engine initialization
- Portfolio creation and management
- Order submission and execution
- Real-time P&L tracking
- Performance metrics calculation

## 📦 Installation & Setup

### Dependencies
```bash
pip install pandas numpy structlog
```

### Environment Variables
Create a `.env` file in the project root:

```env
# Simulation Configuration
SIMULATION_MODE=true
SIMULATION_INITIAL_CAPITAL=10000.0
SIMULATION_COMMISSION=0.001
SIMULATION_SLIPPAGE=0.0001
SIMULATION_TICK_INTERVAL=5.0

# Database Configuration
DB_PATH=./data/app.db
SIMULATION_TABLE_PREFIX=sim_
```

## 🎯 Basic Usage

### Initialize Simulation Engine

```python
from src.simulation.engine import SimulationEngine
from src.simulation.config import SimulationConfig

# Create configuration
config = SimulationConfig(
    initial_capital=10000.0,
    commission=0.001,
    slippage=0.0001,
    tick_interval=5.0
)

# Create simulation engine
engine = SimulationEngine(config)

# Start simulation
await engine.start()
```

### Portfolio Management

```python
# Get portfolio overview
portfolio = await engine.get_portfolio()
print(f"Total Value: ${portfolio.total_value:,.2f}")
print(f"Cash: ${portfolio.cash:,.2f}")
print(f"Positions Value: ${portfolio.positions_value:,.2f}")

# Get open positions
positions = await engine.get_positions()
for position in positions:
    print(f"{position.symbol}: {position.quantity} @ ${position.avg_price:,.2f}")
```

### Order Execution

```python
from src.simulation.orders import MarketOrder

# Create market order
order = MarketOrder(
    symbol="BTCUSDT",
    side="buy",
    quantity=0.1,
    order_type="market"
)

# Submit order
result = await engine.submit_order(order)
print(f"Order executed: {result.status}")
print(f"Execution price: ${result.execution_price:,.2f}")
```

## 🛠️ Core Components

### 1. Simulation Engine

The main simulation controller:

```python
from src.simulation.engine import SimulationEngine

class SimulationEngine:
    """Main simulation engine for paper trading"""
    
    async def start(self) -> None:
        """Start the simulation engine"""
        
    async def stop(self) -> None:
        """Stop the simulation engine"""
        
    async def reset(self) -> None:
        """Reset simulation to initial state"""
        
    async def get_status(self) -> SimulationStatus:
        """Get current simulation status"""
        
    async def submit_order(self, order: Order) -> OrderResult:
        """Submit and execute an order"""
        
    async def get_portfolio(self) -> Portfolio:
        """Get current portfolio information"""
        
    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        
    async def get_trades(self) -> List[Trade]:
        """Get trade history"""
```

### 2. Portfolio Manager

Manages portfolio state and calculations:

```python
from src.simulation.portfolio import PortfolioManager

class PortfolioManager:
    """Manages portfolio state and calculations"""
    
    def update_position(self, symbol: str, quantity: float, 
                       price: float, side: str) -> None:
        """Update position after trade execution"""
        
    def calculate_pnl(self, symbol: str, current_price: float) -> float:
        """Calculate unrealized P&L for position"""
        
    def get_total_value(self) -> float:
        """Get total portfolio value"""
        
    def get_cash_balance(self) -> float:
        """Get available cash balance"""
        
    def get_positions_value(self) -> float:
        """Get total value of all positions"""
```

### 3. Order Manager

Handles order execution and simulation:

```python
from src.simulation.orders import OrderManager

class OrderManager:
    """Manages order execution and simulation"""
    
    async def execute_market_order(self, order: MarketOrder) -> OrderResult:
        """Execute market order with slippage simulation"""
        
    async def execute_limit_order(self, order: LimitOrder) -> OrderResult:
        """Execute limit order when conditions are met"""
        
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        
    def calculate_slippage(self, order: Order, market_data: MarketData) -> float:
        """Calculate slippage based on order size and market conditions"""
```

### 4. Performance Analyzer

Calculates trading performance metrics:

```python
from src.simulation.performance import PerformanceAnalyzer

class PerformanceAnalyzer:
    """Analyzes trading performance and calculates metrics"""
    
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        
    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown"""
        
    def calculate_win_rate(self, trades: List[Trade]) -> float:
        """Calculate win rate"""
        
    def calculate_profit_factor(self, trades: List[Trade]) -> float:
        """Calculate profit factor"""
        
    def generate_report(self) -> PerformanceReport:
        """Generate comprehensive performance report"""
```

## 📊 Data Models

### Portfolio

```python
@dataclass
class Portfolio:
    """Portfolio state and information"""
    total_value: float
    cash: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_fees: float
    last_updated: datetime
```

### Position

```python
@dataclass
class Position:
    """Open trading position"""
    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float
    side: str  # 'long' or 'short'
    entry_time: datetime
    last_updated: datetime
```

### Order

```python
@dataclass
class Order:
    """Trading order"""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    order_type: str  # 'market' or 'limit'
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

### Trade

```python
@dataclass
class Trade:
    """Executed trade"""
    id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    slippage: float
    timestamp: datetime
```

## 🔧 Configuration

### Simulation Configuration

```python
from src.simulation.config import SimulationConfig

config = SimulationConfig(
    initial_capital=10000.0,      # Starting capital
    commission=0.001,             # Commission rate (0.1%)
    slippage=0.0001,             # Slippage rate (0.01%)
    tick_interval=5.0,            # Price update interval (seconds)
    max_positions=10,             # Maximum concurrent positions
    risk_per_trade=0.02,         # Risk per trade (2%)
    enable_stop_loss=True,        # Enable stop loss
    enable_take_profit=True,      # Enable take profit
    data_source="websocket",      # Data source: websocket or historical
    symbols=["BTCUSDT", "ETHUSDT"] # Trading symbols
)
```

### Risk Management Configuration

```python
from src.simulation.risk import RiskConfig

risk_config = RiskConfig(
    max_position_size=0.2,        # Maximum position size (20% of portfolio)
    max_daily_loss=0.05,          # Maximum daily loss (5%)
    max_drawdown=0.15,            # Maximum drawdown (15%)
    correlation_limit=0.7,         # Maximum correlation between positions
    sector_limit=0.3               # Maximum exposure to single sector
)
```

### Performance Configuration

```python
from src.simulation.performance import PerformanceConfig

perf_config = PerformanceConfig(
    benchmark_symbol="BTCUSDT",    # Benchmark for performance comparison
    risk_free_rate=0.02,          # Risk-free rate (2%)
    rolling_window=30,             # Rolling window for metrics (days)
    save_snapshots=True,           # Save portfolio snapshots
    snapshot_interval=300          # Snapshot interval (seconds)
)
```

## 📈 Performance Metrics

### Basic Metrics

```python
# Get basic performance metrics
metrics = await engine.get_performance_metrics()

print(f"Total Return: {metrics.total_return:.2%}")
print(f"Annualized Return: {metrics.annualized_return:.2%}")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown:.2%}")
print(f"Win Rate: {metrics.win_rate:.2%}")
print(f"Profit Factor: {metrics.profit_factor:.2f}")
```

### Advanced Metrics

```python
# Get advanced performance metrics
advanced_metrics = await engine.get_advanced_metrics()

print(f"Calmar Ratio: {advanced_metrics.calmar_ratio:.2f}")
print(f"Sortino Ratio: {advanced_metrics.sortino_ratio:.2f}")
print(f"Information Ratio: {advanced_metrics.information_ratio:.2f}")
print(f"Value at Risk (95%): {advanced_metrics.var_95:.2%}")
print(f"Expected Shortfall: {advanced_metrics.expected_shortfall:.2%}")
```

### Risk Metrics

```python
# Get risk metrics
risk_metrics = await engine.get_risk_metrics()

print(f"Volatility: {risk_metrics.volatility:.2%}")
print(f"Beta: {risk_metrics.beta:.2f}")
print(f"Alpha: {risk_metrics.alpha:.2%}")
print(f"Correlation: {risk_metrics.correlation:.2f}")
print(f"Tracking Error: {risk_metrics.tracking_error:.2%}")
```

## 🚨 Error Handling

### Common Errors

#### 1. Insufficient Funds
```python
try:
    order = MarketOrder(symbol="BTCUSDT", side="buy", quantity=1000.0)
    result = await engine.submit_order(order)
except InsufficientFundsError as e:
    print(f"Insufficient funds: {e}")
    print(f"Available cash: ${engine.get_portfolio().cash:,.2f}")
```

#### 2. Invalid Order
```python
try:
    order = MarketOrder(symbol="INVALID", side="buy", quantity=0.1)
    result = await engine.submit_order(order)
except InvalidOrderError as e:
    print(f"Invalid order: {e}")
```

#### 3. Simulation Not Running
```python
try:
    await engine.submit_order(order)
except SimulationNotRunningError:
    print("Simulation engine is not running")
    await engine.start()
```

### Error Recovery

```python
from src.simulation.errors import SimulationError

async def safe_order_execution(order: Order):
    """Safely execute order with error handling"""
    try:
        result = await engine.submit_order(order)
        return result
    except SimulationError as e:
        logger.error(f"Order execution failed: {e}")
        # Implement recovery logic
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
```

## 📊 Data Storage

### Database Tables

The simulation engine uses separate database tables with `sim_` prefix:

```sql
-- Portfolio snapshots
CREATE TABLE sim_portfolio_snapshots (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    total_value REAL NOT NULL,
    cash REAL NOT NULL,
    positions_value REAL NOT NULL,
    unrealized_pnl REAL NOT NULL,
    realized_pnl REAL NOT NULL
);

-- Trades
CREATE TABLE sim_trades (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    commission REAL NOT NULL,
    slippage REAL NOT NULL,
    timestamp DATETIME NOT NULL
);

-- Positions
CREATE TABLE sim_positions (
    symbol TEXT PRIMARY KEY,
    quantity REAL NOT NULL,
    avg_price REAL NOT NULL,
    side TEXT NOT NULL,
    entry_time DATETIME NOT NULL,
    last_updated DATETIME NOT NULL
);
```

### Data Export

```python
# Export portfolio data to CSV
await engine.export_portfolio_data("portfolio_data.csv")

# Export trade history to CSV
await engine.export_trade_history("trade_history.csv")

# Export performance report to JSON
await engine.export_performance_report("performance_report.json")
```

## 🧪 Testing

### Unit Tests

```bash
# Run simulation engine tests
pytest tests/test_simulation/ -v

# Run specific test file
pytest tests/test_simulation/test_engine.py -v

# Run with coverage
pytest tests/test_simulation/ --cov=src.simulation
```

### Integration Tests

```bash
# Run integration tests
pytest tests/test_simulation/ -m integration

# Test with real data feeds
pytest tests/test_simulation/ --env=live
```

### Performance Tests

```bash
# Run performance benchmarks
pytest tests/test_simulation/ -m performance

# Test with large datasets
pytest tests/test_simulation/ --env=stress
```

## 🔒 Security

### Data Isolation

- Separate database tables for simulation data
- No access to live trading systems
- Complete isolation from production environment
- Safe for development and testing

### Input Validation

- Validate all order parameters
- Check position limits and risk parameters
- Sanitize user inputs
- Prevent invalid operations

### Audit Trail

- Log all simulation activities
- Track order execution history
- Monitor portfolio changes
- Maintain complete audit trail

## 📊 Monitoring

### Health Checks

```python
from src.simulation.monitoring import SimulationMonitor

monitor = SimulationMonitor()

# Check simulation health
health = await monitor.check_health()
print(f"Simulation status: {health.status}")
print(f"Uptime: {health.uptime}")
print(f"Active positions: {health.active_positions}")

# Get performance alerts
alerts = await monitor.get_alerts()
for alert in alerts:
    print(f"Alert: {alert.message} (Level: {alert.level})")
```

### Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Log simulation events
logger.info("Simulation started", 
           initial_capital=config.initial_capital,
           symbols=config.symbols)

# Log order execution
logger.info("Order executed", 
           order_id=result.order_id,
           symbol=result.symbol,
           quantity=result.quantity,
           price=result.execution_price)

# Log portfolio changes
logger.info("Portfolio updated", 
           total_value=portfolio.total_value,
           cash=portfolio.cash,
           positions_value=portfolio.positions_value)
```

## 🤝 Contributing

### Adding New Features

1. Create feature branch from main
2. Implement new functionality
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

### Reporting Issues

1. Check the troubleshooting section first
2. Provide error messages and stack traces
3. Include your environment details
4. Describe what you were trying to do

### Getting Help

- Check the main project README
- Look at existing examples
- Run the demo scripts
- Create a minimal reproduction of your issue

## 📝 License

This package is part of the Smart Trading Bot project and follows the same license terms.

---

**Happy Trading! 🚀**

*Remember: Simulation mode is for testing strategies. Always validate thoroughly before live trading.*
