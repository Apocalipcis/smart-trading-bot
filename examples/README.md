# Examples

This directory contains demonstration scripts for the smart-trading-bot package, showcasing all major features including the simulation engine.

## Running the Examples

### Option 1: Direct Python Execution
```bash
# From the project root directory
python examples/backtest_demo.py
python examples/simulation_demo.py
```

### Option 2: As a Module
```bash
# From the project root directory
python -m examples
```

### Option 3: Install in Development Mode (Recommended)
```bash
# Install the package in development mode to resolve import issues
python install_dev.py

# Then run examples normally
python examples/backtest_demo.py
```

## Available Examples

### 1. backtest_demo.py
Demonstrates the core functionality of the backtests package:

- **Storage Demo**: Shows how to save and load backtest results
- **Metrics Demo**: Demonstrates performance and risk metrics calculation
- **Data Integrity Demo**: Shows data quality checking and fixing

**What You'll See:**
- Backtest storage operations (save/load)
- Performance metrics calculation
- Risk analysis (drawdown, VaR, etc.)
- Data integrity checking
- Data quality issue detection and fixing

### 2. simulation_demo.py (NEW)
Demonstrates the complete simulation engine functionality:

- **Simulation Engine Setup**: Initialize and configure the simulation engine
- **Portfolio Management**: Track positions, cash, and P&L
- **Order Processing**: Submit and execute orders with slippage and commission
- **Performance Tracking**: Monitor portfolio performance and metrics
- **Real-time Updates**: Handle price updates and position management

**What You'll See:**
- Simulation engine initialization
- Portfolio creation and management
- Order submission and execution
- Real-time P&L tracking
- Performance metrics calculation
- Position management examples

### 3. data_layer_demo.py
Demonstrates the data layer functionality:

- **Binance Client**: REST API and WebSocket connections
- **Data Validation**: Exchange rules and constraints
- **Rate Limiting**: API rate limit management
- **WebSocket Streaming**: Real-time data feeds

**What You'll See:**
- Exchange information retrieval
- Historical data download
- Real-time price streaming
- Data validation examples
- Rate limiting demonstrations

### 4. strategy_demo.py
Demonstrates the trading strategy system:

- **Strategy Registry**: Auto-discovery of strategy files
- **SMC Strategy**: Smart Money Concepts implementation
- **Signal Generation**: Create and validate trading signals
- **Custom Strategies**: Build and test custom strategies

**What You'll See:**
- Strategy registry discovery
- SMC strategy information
- Sample signal generation
- Custom strategy examples
- Signal validation

### 5. download_data_demo.py
Demonstrates historical data download and management:

- **Data Download**: Download historical candle data from Binance
- **Data Storage**: Save data in Parquet format
- **Data Validation**: Check data quality and integrity
- **Data Management**: Organize and manage historical data

**What You'll See:**
- Historical data download
- Data storage operations
- Data quality checks
- File organization examples

## Quick Start Guide

### 1. Setup Environment
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
```

### 2. Run Basic Examples
```bash
# Start with data layer demo
python examples/data_layer_demo.py

# Then try strategy demo
python examples/strategy_demo.py

# Run backtest demo
python examples/backtest_demo.py

# Finally, try simulation demo
python examples/simulation_demo.py
```

### 3. Interactive Exploration
```bash
# Start Python REPL with examples
python -i examples/simulation_demo.py

# Or run specific functions
python -c "
from examples.simulation_demo import run_basic_simulation
run_basic_simulation()
"
```

## Example Outputs

### Simulation Demo Output
```
🚀 Starting Simulation Demo...

📊 Simulation Engine Status:
- Running: True
- Mode: simulation
- Portfolio Value: $10,000.00
- Positions: 0
- Orders: 0

💰 Portfolio Overview:
- Total Value: $10,000.00
- Cash: $10,000.00
- Positions Value: $0.00
- Unrealized P&L: $0.00

📈 Performance Metrics:
- Total Return: 0.00%
- Sharpe Ratio: 0.00
- Max Drawdown: 0.00%
- Win Rate: 0.00%

✅ Simulation Demo Completed Successfully!
```

### Backtest Demo Output
```
🧪 Starting Backtest Demo...

📊 Backtest Results:
- Strategy: SMC
- Pair: BTCUSDT
- Timeframe: 1m
- Total Return: 15.5%
- Win Rate: 68%
- Total Trades: 45

📈 Performance Metrics:
- Sharpe Ratio: 1.85
- Max Drawdown: -8.5%
- Profit Factor: 2.1

✅ Backtest Demo Completed Successfully!
```

## Configuration

### Environment Setup
Create a `.env` file in the project root:

```env
# Trading Configuration
TRADING_MODE=simulation
TRADING_APPROVED=false

# Simulation Settings
SIMULATION_INITIAL_CAPITAL=10000.0
SIMULATION_COMMISSION=0.001
SIMULATION_SLIPPAGE=0.0001

# Exchange Configuration
EXCHANGE=binance_futures
WS_URL=wss://fstream.binance.com/ws
REST_URL=https://fapi.binance.com

# Data Storage
DATA_DIR=./data
DB_PATH=./data/app.db
```

### Example-Specific Configuration
Each example can be configured independently:

```python
# simulation_demo.py configuration
SIMULATION_CONFIG = {
    "initial_capital": 10000.0,
    "commission": 0.001,
    "slippage": 0.0001,
    "tick_interval": 5.0
}

# backtest_demo.py configuration
BACKTEST_CONFIG = {
    "pair": "BTCUSDT",
    "strategy": "SMC",
    "timeframe": "1m",
    "start_date": "2024-01-01",
    "end_date": "2024-01-15"
}
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Solution: Install in development mode
python install_dev.py

# Or add src to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### Missing Dependencies
```bash
# Install all dependencies
pip install -e ".[dev]"

# Or install specific packages
pip install backtrader pandas numpy fastapi
```

#### Database Errors
```bash
# Create data directory
mkdir -p data

# Initialize database
python -c "from src.storage.db import init_db; init_db()"
```

#### WebSocket Connection Issues
```bash
# Check network connectivity
curl -I https://fapi.binance.com

# Test WebSocket connection
python -c "
import asyncio
from src.data.binance_client import BinanceClient
async def test():
    client = BinanceClient()
    await client.connect()
    print('Connection successful')
asyncio.run(test())
"
```

### Debug Mode
Enable debug logging for detailed output:

```bash
# Set debug environment variable
export DEBUG_MODE=true

# Or modify examples to enable debug
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from examples.simulation_demo import run_basic_simulation
run_basic_simulation()
"
```

## Advanced Usage

### Custom Example Development
Create your own examples:

```python
# my_custom_demo.py
import sys
sys.path.insert(0, 'src')

from simulation.engine import SimulationEngine
from simulation.config import SimulationConfig

def run_custom_demo():
    # Your custom demo code here
    config = SimulationConfig(initial_capital=50000.0)
    engine = SimulationEngine(config)
    
    # Custom logic...
    print("Custom demo completed!")

if __name__ == "__main__":
    run_custom_demo()
```

### Integration Examples
Combine multiple features:

```python
# integration_demo.py
from examples.simulation_demo import run_basic_simulation
from examples.strategy_demo import run_strategy_demo
from examples.backtest_demo import run_backtest_demo

def run_integration_demo():
    print("🧪 Running Integration Demo...")
    
    # Run strategy demo
    run_strategy_demo()
    
    # Run backtest demo
    run_backtest_demo()
    
    # Run simulation demo
    run_basic_simulation()
    
    print("✅ Integration Demo Completed!")

if __name__ == "__main__":
    run_integration_demo()
```

## Performance Testing

### Benchmark Examples
Test performance with different configurations:

```python
# performance_demo.py
import time
from examples.simulation_demo import run_basic_simulation

def benchmark_simulation():
    start_time = time.time()
    
    # Run simulation
    run_basic_simulation()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️ Simulation completed in {duration:.2f} seconds")

if __name__ == "__main__":
    benchmark_simulation()
```

## Next Steps

After running the examples, you can:

1. **Explore the Source Code**: 
   - Check `src/simulation/` for simulation engine
   - Check `src/strategies/` for trading strategies
   - Check `src/data/` for data layer

2. **Run the Test Suite**:
   ```bash
   pytest tests/
   ```

3. **Start the API Server**:
   ```bash
   uvicorn src.api.main:app --reload
   ```

4. **Access Interactive Documentation**:
   - Open `http://localhost:8000/docs` in your browser

5. **Build Custom Strategies**:
   - Create new strategies in `src/strategies/`
   - Test with simulation engine
   - Backtest for validation

## Requirements

- Python 3.8+
- Virtual environment activated
- Required packages installed (pandas, numpy, backtrader, etc.)
- Internet connection for data access
- Sufficient disk space for data storage

## Support

For issues with examples:

1. Check the troubleshooting section above
2. Review the main project README
3. Check the source code documentation
4. Create a minimal reproduction of your issue
5. Submit an issue with detailed error information

## Changelog

### v1.0.0
- Added simulation_demo.py
- Updated all examples for latest API
- Added comprehensive troubleshooting
- Added performance testing examples
- Added integration examples
- Improved documentation and configuration
