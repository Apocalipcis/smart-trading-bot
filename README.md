# Smart Trading Bot

A professional trading bot built with Python, FastAPI, and Backtrader for cryptocurrency trading on Binance Futures with comprehensive simulation capabilities.

## 🚀 Features

- **Real-time Data**: WebSocket streaming from Binance USDT-M Futures
- **Backtesting Engine**: Full Backtrader integration with historical data
- **Trading Strategies**: Plugin-based strategy system with Smart Money Concepts (SMC)
- **Risk Management**: Configurable position sizing, stop-loss, and take-profit
- **Simulation Engine**: Complete paper trading environment with dual-mode support
- **Web Interface**: Modern SPA dashboard for monitoring and control
- **Telegram Notifications**: Real-time alerts for signals and backtest results
- **API-First Design**: RESTful API with WebSocket/SSE streaming support

## 🏗️ Architecture

```
smart-trading-bot/
├── src/                    # Backend source code
│   ├── api/               # FastAPI application
│   │   ├── routers/       # API endpoints
│   │   ├── schemas.py     # Pydantic models
│   │   ├── dependencies.py # Dependency injection
│   │   └── middleware.py  # Logging & correlation IDs
│   ├── data/              # Data layer (✅ COMPLETED)
│   │   ├── binance_client.py
│   │   ├── stream.py
│   │   ├── feed.py
│   │   ├── validators.py
│   │   └── rate_limit.py
│   ├── backtests/         # Backtesting engine
│   ├── strategies/        # Trading strategies (✅ COMPLETED)
│   ├── orders/            # Order management
│   ├── simulation/        # Simulation engine (✅ COMPLETED)
│   └── storage/           # Database & file storage
├── web/                   # Frontend SPA
├── data/                  # Persistent data storage
├── tests/                 # Test suite
└── docker/                # Containerization
```

## 📋 Current Status

### ✅ Completed
- **Data Layer**: Complete Binance integration with WebSocket streaming
- **API Layer**: Full FastAPI implementation with all endpoints
- **Strategies Package**: Complete trading strategy system with SMC implementation
- **Simulation Engine**: Complete paper trading environment with portfolio management
- **Structured Logging**: JSON logs with correlation IDs
- **Telegram Integration**: Rich notification system
- **Health Monitoring**: System status and metrics
- **Testing**: Pytest setup with working tests

### 🔄 In Progress
- **Backtesting Engine**: Backtrader integration
- **Order Management**: Position sizing and execution
- **Storage Layer**: Database and file management

### 📝 Planned
- **Web UI**: React/Vite frontend
- **Docker**: Containerization
- **CI/CD**: GitHub Actions pipeline

## 🎯 Trading Modes

The bot supports two distinct trading modes:

### Simulation Mode (Default)
- **Paper Trading**: Risk-free environment for strategy testing
- **Real-time Data**: Uses actual WebSocket price feeds
- **Portfolio Management**: Full P&L tracking and position management
- **No API Keys Required**: Safe for development and testing
- **Complete Isolation**: Separate database tables and storage

### Live Trading Mode
- **Real Trading**: Actual order execution on Binance Futures
- **Approval Required**: Explicit approval needed for live trading
- **API Keys Required**: Valid Binance API credentials
- **Risk Management**: Comprehensive position and risk controls
- **Audit Trail**: Complete logging of all trading activities

## 🎯 Trading Strategies

The bot includes a comprehensive strategy system built on Backtrader:

### Base Strategy Class
- **Abstract base class** with enforced signal contract
- **Risk management** with configurable parameters
- **Position sizing** based on risk percentage
- **Signal validation** with minimum risk-reward ratios

### Smart Money Concepts (SMC) Strategy
- **Institutional order flow** analysis
- **Liquidity zone** identification
- **Order block** detection
- **Fair value gap** analysis
- **Market structure** trend confirmation

### Strategy Registry
- **Auto-discovery** of strategy files
- **Version management** and validation
- **Plugin system** for easy strategy addition
- **Parameter extraction** and documentation

### Signal Contract
All strategies must implement the standard signal format:
```python
Signal(
    side='long' | 'short',
    entry=float,           # Entry price
    stop_loss=float,       # Stop loss price
    take_profit=float,     # Take profit price
    confidence=float,      # 0.0-1.0 confidence
    metadata=dict          # Strategy-specific data
)
```

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/smart-trading-bot.git
cd smart-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies using modern Python packaging
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### Alternative Installation Methods

#### Using pip with pyproject.toml
```bash
pip install -e .
```

#### Using pip with development dependencies
```bash
pip install -e ".[dev]"
```

#### Using uv (recommended for development)
```bash
# Install uv if you don't have it
pip install uv

# Install dependencies
uv sync
```

## 🧪 Testing

The project uses pytest with comprehensive configuration in `pyproject.toml`:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest -m "not slow"
pytest -m "integration"
```

## 🔧 Development Tools

The project is configured with modern Python development tools:

- **Ruff**: Fast Python linter and formatter
- **Black**: Code formatting
- **MyPy**: Static type checking
- **Pytest**: Testing framework

All tools are configured in `pyproject.toml` for consistency.

## 📁 Project Structure

```
smart-trading-bot/
├── pyproject.toml         # Project configuration (dependencies, tools)
├── conftest.py           # Pytest configuration and fixtures
├── .gitignore            # Git ignore patterns
├── src/                  # Source code
│   ├── api/             # FastAPI application
│   ├── data/            # Data layer
│   ├── strategies/      # Trading strategies
│   ├── simulation/      # Simulation engine
│   └── backtests/       # Backtesting engine
├── tests/               # Test suite
├── examples/            # Usage examples
└── docs/               # Documentation
```

## 🚀 Why This Structure?

- **pyproject.toml**: Modern Python standard (PEP 518, PEP 621)
- **No setup.py**: Replaced by pyproject.toml for better maintainability
- **No requirements.txt**: Dependencies managed centrally in pyproject.toml
- **conftest.py**: Essential for pytest configuration and shared fixtures
- **Modern tooling**: Ruff, Black, MyPy configured in pyproject.toml

## 📚 Documentation

### Core Documentation
- **[Technical Specification](trading_bot_spec.md)**: Complete technical overview
- **[Simulation Engine](SIMULATION_ENGINE.md)**: Paper trading environment
- **[Infrastructure](INFRASTRUCTURE.md)**: Deployment and monitoring
- **[Debug Guide](DEBUG.md)**: Development and troubleshooting

### Component Documentation
- **[Data Layer](src/data/README.md)**: Binance integration and data handling
- **[Strategies](src/strategies/README.md)**: Trading strategy system
- **[Examples](examples/README.md)**: Usage examples and demos

### API Documentation
- **Interactive API Docs**: Available at `/docs` when running the server
- **OpenAPI Schema**: Available at `/openapi.json`
- **API Examples**: See `examples/` directory for usage examples

## 🚨 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Solution: Install in development mode
python install_dev.py

# Or activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### Docker Build Issues
```bash
# Use debug build for detailed logging
bash scripts/debug-build.sh

# Or build with verbose output
docker build -f Dockerfile.debug -t smart-trading-bot:debug .
```

#### API Connection Issues
```bash
# Check if server is running
curl http://localhost:8000/api/v1/status/health

# Check logs
docker-compose logs -f trading-bot
```

#### Simulation Engine Issues
```bash
# Reset simulation
curl -X POST http://localhost:8000/api/v1/simulation/reset

# Check simulation status
curl http://localhost:8000/api/v1/simulation/status
```

### Performance Issues

#### High Memory Usage
- Reduce simulation tick intervals
- Limit portfolio snapshots
- Clear old data periodically

#### Slow API Responses
- Check database performance
- Monitor WebSocket connections
- Review rate limiting settings

### Debug Mode

Enable debug logging:
```bash
# Set environment variable
export DEBUG_MODE=true

# Or in .env file
DEBUG_MODE=true
```

## 🔒 Security

### API Key Management
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate keys regularly
- Use read-only keys for testing

### Live Trading Protection
- Explicit approval required for live trading
- Simulation mode by default
- Complete audit trail
- Risk management controls

## 📊 Monitoring

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/api/v1/status/health

# Detailed health check
curl http://localhost:8000/api/v1/status/health/detailed

# System metrics
curl http://localhost:8000/api/v1/status/metrics
```

### Logging
- Structured JSON logging
- Correlation IDs for request tracking
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests and linting
5. Submit a pull request

### Code Quality
```bash
# Run linting
ruff check src/

# Format code
black src/

# Type checking
mypy src/

# Run tests
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes. Trading cryptocurrencies involves substantial risk of loss. Always test strategies thoroughly in simulation mode before using real money. The authors are not responsible for any financial losses incurred through the use of this software.

---

**Happy Trading! 🚀**

*Remember: Start with simulation mode and always use proper risk management.*
