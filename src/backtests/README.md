# Backtesting Engine Package

A comprehensive backtesting engine for the Smart Trading Bot that provides multi-timeframe strategy testing, performance analysis, and result management using Backtrader integration.

## 🚀 Quick Start

### What This Package Does
- **Multi-Timeframe Backtesting**: Support for HTF/LTF analysis with role-based timeframes
- **Strategy Testing**: Comprehensive testing of trading strategies using Backtrader
- **Performance Metrics**: Complete performance and risk analysis
- **Result Management**: Storage, retrieval, and analysis of backtest results
- **Data Integration**: Seamless integration with historical data feeds

### Run the Demo (5 minutes)
```bash
# From project root
cd examples
python backtest_demo.py
```

You should see:
- Backtest storage operations (save/load)
- Performance metrics calculation
- Risk analysis (drawdown, VaR, etc.)
- Data integrity checking
- Multi-timeframe backtest examples

## 📦 Installation & Setup

### Dependencies
```bash
pip install backtrader pandas numpy pyarrow
```

### Environment Variables
Create a `.env` file in the project root:

```env
# Backtesting Configuration
BACKTEST_DATA_DIR=./data/candles
BACKTEST_RESULTS_DIR=./data/backtests
BACKTEST_ARTIFACTS_DIR=./data/artifacts

# Database Configuration
DB_PATH=./data/app.db
```

## 🎯 Basic Usage

### Simple Backtest

```python
from src.backtests.engine import BacktestEngine
from src.backtests.config import BacktestConfig

# Create backtest configuration
config = BacktestConfig(
    symbol="BTCUSDT",
    strategy="SMC",
    start_date="2024-01-01",
    end_date="2024-01-07",
    timeframes=["1h"],
    initial_balance=10000.0,
    commission=0.001
)

# Create backtest engine
engine = BacktestEngine()

# Run backtest
result = await engine.run_backtest(config)
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

### Multi-Timeframe Backtest

```python
# Multi-timeframe configuration
config = BacktestConfig(
    symbol="BTCUSDT",
    strategy="SMC",
    start_date="2024-01-01",
    end_date="2024-01-07",
    timeframes=["4h", "1h"],
    tf_roles={"4h": "HTF", "1h": "LTF"},
    initial_balance=10000.0,
    commission=0.001
)

# Run multi-timeframe backtest
result = await engine.run_backtest(config)
print(f"HTF Analysis: {result.htf_analysis}")
print(f"LTF Analysis: {result.ltf_analysis}")
```

## 🛠️ Core Components

### 1. Backtest Engine

The main backtesting controller:

```python
from src.backtests.engine import BacktestEngine

class BacktestEngine:
    """Main backtesting engine using Backtrader"""
    
    async def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Run a complete backtest"""
        
    async def run_multi_timeframe_backtest(self, config: BacktestConfig) -> MultiTimeframeResult:
        """Run multi-timeframe backtest"""
        
    async def validate_data(self, config: BacktestConfig) -> DataValidationResult:
        """Validate data availability and quality"""
        
    async def get_available_strategies(self) -> List[str]:
        """Get list of available strategies"""
        
    async def get_available_timeframes(self) -> List[str]:
        """Get list of available timeframes"""
```

### 2. Backtest Configuration

Configuration management for backtests:

```python
from src.backtests.config import BacktestConfig

@dataclass
class BacktestConfig:
    """Backtest configuration parameters"""
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    timeframes: List[str]
    tf_roles: Optional[Dict[str, str]] = None
    initial_balance: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.0001
    max_positions: int = 5
    risk_per_trade: float = 0.02
    min_risk_reward: float = 3.0
```

### 3. Data Manager

Handles data loading and validation:

```python
from src.backtests.data import DataManager

class DataManager:
    """Manages data loading and validation for backtests"""
    
    async def load_data(self, symbol: str, timeframe: str, 
                       start_date: str, end_date: str) -> pd.DataFrame:
        """Load historical data for backtest"""
        
    async def validate_data_quality(self, data: pd.DataFrame) -> DataQualityReport:
        """Validate data quality and integrity"""
        
    async def check_data_coverage(self, symbol: str, timeframe: str,
                                 start_date: str, end_date: str) -> CoverageReport:
        """Check data coverage for specified period"""
        
    async def get_data_info(self, symbol: str, timeframe: str) -> DataInfo:
        """Get information about available data"""
```

### 4. Strategy Loader

Loads and validates trading strategies:

```python
from src.backtests.strategies import StrategyLoader

class StrategyLoader:
    """Loads and validates trading strategies"""
    
    def load_strategy(self, strategy_name: str) -> Type[bt.Strategy]:
        """Load strategy class by name"""
        
    def validate_strategy(self, strategy_class: Type[bt.Strategy]) -> ValidationResult:
        """Validate strategy implementation"""
        
    def get_strategy_parameters(self, strategy_class: Type[bt.Strategy]) -> Dict[str, Any]:
        """Get strategy parameters and defaults"""
        
    def get_strategy_info(self, strategy_name: str) -> StrategyInfo:
        """Get strategy information and metadata"""
```

### 5. Result Manager

Manages backtest results and storage:

```python
from src.backtests.results import ResultManager

class ResultManager:
    """Manages backtest results and storage"""
    
    async def save_result(self, result: BacktestResult) -> str:
        """Save backtest result to storage"""
        
    async def load_result(self, result_id: str) -> BacktestResult:
        """Load backtest result from storage"""
        
    async def list_results(self, filters: Optional[Dict[str, Any]] = None) -> List[BacktestResult]:
        """List stored backtest results"""
        
    async def delete_result(self, result_id: str) -> bool:
        """Delete backtest result"""
        
    async def export_result(self, result_id: str, format: str) -> bytes:
        """Export result in specified format"""
```

## 📊 Data Models

### Backtest Result

```python
@dataclass
class BacktestResult:
    """Complete backtest result"""
    id: str
    symbol: str
    strategy: str
    start_date: datetime
    end_date: datetime
    timeframes: List[str]
    tf_roles: Optional[Dict[str, str]]
    initial_balance: float
    final_balance: float
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    profit_factor: float
    avg_trade: float
    avg_win: float
    avg_loss: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    created_at: datetime
    metadata: Dict[str, Any]
```

### Multi-Timeframe Result

```python
@dataclass
class MultiTimeframeResult(BacktestResult):
    """Multi-timeframe backtest result"""
    htf_analysis: Dict[str, Any]
    ltf_analysis: Dict[str, Any]
    timeframe_correlation: float
    combined_metrics: Dict[str, Any]
```

### Data Validation Result

```python
@dataclass
class DataValidationResult:
    """Data validation result"""
    is_valid: bool
    data_points: int
    start_date: datetime
    end_date: datetime
    gaps: List[DataGap]
    duplicates: List[DataDuplicate]
    anomalies: List[DataAnomaly]
    quality_score: float
    warnings: List[str]
    errors: List[str]
```

## 🔧 Configuration

### Backtest Configuration

```python
from src.backtests.config import BacktestConfig

config = BacktestConfig(
    symbol="BTCUSDT",
    strategy="SMC",
    start_date="2024-01-01",
    end_date="2024-01-07",
    timeframes=["4h", "1h"],
    tf_roles={"4h": "HTF", "1h": "LTF"},
    initial_balance=10000.0,
    commission=0.001,
    slippage=0.0001,
    max_positions=5,
    risk_per_trade=0.02,
    min_risk_reward=3.0
)
```

### Strategy Configuration

```python
from src.backtests.strategy_config import StrategyConfig

strategy_config = StrategyConfig(
    risk_per_trade=0.02,        # Risk per trade (2%)
    position_size=0.1,          # Position size (10%)
    use_stop_loss=True,         # Enable stop loss
    use_take_profit=True,       # Enable take profit
    min_risk_reward=3.0,        # Minimum risk-reward ratio
    max_positions=5,            # Maximum concurrent positions
    lookback_period=30,         # Lookback period for indicators
    volume_threshold=2.0        # Volume threshold multiplier
)
```

### Performance Configuration

```python
from src.backtests.performance_config import PerformanceConfig

perf_config = PerformanceConfig(
    benchmark_symbol="BTCUSDT",    # Benchmark for comparison
    risk_free_rate=0.02,          # Risk-free rate (2%)
    rolling_window=30,             # Rolling window (days)
    save_equity_curve=True,        # Save equity curve
    save_trade_log=True,           # Save detailed trade log
    save_portfolio_snapshots=True, # Save portfolio snapshots
    snapshot_interval=3600         # Snapshot interval (seconds)
)
```

## 📈 Performance Metrics

### Basic Metrics

```python
# Get basic performance metrics
metrics = result.get_basic_metrics()

print(f"Total Return: {metrics.total_return:.2%}")
print(f"Annualized Return: {metrics.annualized_return:.2%}")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown:.2%}")
print(f"Win Rate: {metrics.win_rate:.2%}")
print(f"Total Trades: {metrics.total_trades}")
```

### Risk Metrics

```python
# Get risk metrics
risk_metrics = result.get_risk_metrics()

print(f"Volatility: {risk_metrics.volatility:.2%}")
print(f"Value at Risk (95%): {risk_metrics.var_95:.2%}")
print(f"Expected Shortfall: {risk_metrics.expected_shortfall:.2%}")
print(f"Downside Deviation: {risk_metrics.downside_deviation:.2%}")
print(f"Calmar Ratio: {risk_metrics.calmar_ratio:.2f}")
```

### Advanced Metrics

```python
# Get advanced metrics
advanced_metrics = result.get_advanced_metrics()

print(f"Sortino Ratio: {advanced_metrics.sortino_ratio:.2f}")
print(f"Information Ratio: {advanced_metrics.information_ratio:.2f}")
print(f"Treynor Ratio: {advanced_metrics.treynor_ratio:.2f}")
print(f"Jensen's Alpha: {advanced_metrics.jensens_alpha:.2%}")
print(f"Tracking Error: {advanced_metrics.tracking_error:.2%}")
```

## 🚨 Error Handling

### Common Errors

#### 1. Insufficient Data
```python
try:
    result = await engine.run_backtest(config)
except InsufficientDataError as e:
    print(f"Insufficient data: {e}")
    print(f"Available data: {e.available_start} to {e.available_end}")
```

#### 2. Strategy Not Found
```python
try:
    result = await engine.run_backtest(config)
except StrategyNotFoundError as e:
    print(f"Strategy not found: {e}")
    available = await engine.get_available_strategies()
    print(f"Available strategies: {available}")
```

#### 3. Invalid Configuration
```python
try:
    result = await engine.run_backtest(config)
except InvalidConfigError as e:
    print(f"Invalid configuration: {e}")
    print(f"Validation errors: {e.errors}")
```

### Error Recovery

```python
from src.backtests.errors import BacktestError

async def safe_backtest(config: BacktestConfig):
    """Safely run backtest with error handling"""
    try:
        # Validate configuration first
        validation = await engine.validate_config(config)
        if not validation.is_valid:
            print(f"Configuration validation failed: {validation.errors}")
            return None
        
        # Run backtest
        result = await engine.run_backtest(config)
        return result
        
    except BacktestError as e:
        logger.error(f"Backtest failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
```

## 📊 Data Storage

### Database Tables

The backtesting engine uses dedicated database tables:

```sql
-- Backtest results
CREATE TABLE backtest_results (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    timeframes TEXT NOT NULL,
    tf_roles TEXT,
    initial_balance REAL NOT NULL,
    final_balance REAL NOT NULL,
    total_return REAL NOT NULL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    win_rate REAL,
    total_trades INTEGER,
    created_at DATETIME NOT NULL,
    metadata TEXT
);

-- Backtest artifacts
CREATE TABLE backtest_artifacts (
    id TEXT PRIMARY KEY,
    backtest_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(id)
);
```

### File Storage

Backtest results are also stored as files:

```
/data/backtests/
├── 2024-01-15/
│   ├── BTCUSDT_SMC_1h_20240101_20240107.json
│   ├── BTCUSDT_SMC_4h_1h_20240101_20240107.json
│   └── ETHUSDT_SMC_1h_20240101_20240107.json
└── 2024-01-16/
    └── BTCUSDT_SIMPLE_TEST_1h_20240108_20240114.json

/data/artifacts/
├── charts/
│   ├── BTCUSDT_SMC_1h_20240101_20240107.png
│   └── BTCUSDT_SMC_4h_1h_20240101_20240107.png
└── reports/
    ├── BTCUSDT_SMC_1h_20240101_20240107.html
    └── BTCUSDT_SMC_4h_1h_20240101_20240107.html
```

## 🧪 Testing

### Unit Tests

```bash
# Run backtesting engine tests
pytest tests/test_backtests/ -v

# Run specific test file
pytest tests/test_backtests/test_engine.py -v

# Run with coverage
pytest tests/test_backtests/ --cov=src.backtests
```

### Integration Tests

```bash
# Run integration tests
pytest tests/test_backtests/ -m integration

# Test with real data
pytest tests/test_backtests/ --env=live
```

### Performance Tests

```bash
# Run performance benchmarks
pytest tests/test_backtests/ -m performance

# Test with large datasets
pytest tests/test_backtests/ --env=stress
```

## 🔒 Security

### Data Validation

- Validate all input parameters
- Check data integrity before backtesting
- Sanitize strategy parameters
- Prevent malicious code execution

### Result Isolation

- Separate storage for backtest results
- No access to live trading systems
- Safe for development and testing
- Complete audit trail

### Access Control

- Validate user permissions
- Log all backtest operations
- Monitor resource usage
- Prevent abuse

## 📊 Monitoring

### Health Checks

```python
from src.backtests.monitoring import BacktestMonitor

monitor = BacktestMonitor()

# Check backtest engine health
health = await monitor.check_health()
print(f"Backtest engine status: {health.status}")
print(f"Active backtests: {health.active_backtests}")
print(f"Queue length: {health.queue_length}")

# Get performance metrics
metrics = await monitor.get_metrics()
print(f"Average backtest time: {metrics.avg_backtest_time:.2f}s")
print(f"Success rate: {metrics.success_rate:.2%}")
```

### Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Log backtest start
logger.info("Backtest started", 
           symbol=config.symbol,
           strategy=config.strategy,
           start_date=config.start_date,
           end_date=config.end_date)

# Log backtest completion
logger.info("Backtest completed", 
           result_id=result.id,
           total_return=result.total_return,
           sharpe_ratio=result.sharpe_ratio,
           duration=duration)

# Log errors
logger.error("Backtest failed", 
            error=str(e),
            config=config.dict())
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

*Remember: Backtesting is essential for strategy validation. Always test thoroughly before live trading.*
