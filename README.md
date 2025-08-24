# Smart Trading Bot

A professional trading bot built with Python, FastAPI, and Backtrader for cryptocurrency trading on Binance Futures.

## 🚀 Features

- **Real-time Data**: WebSocket streaming from Binance USDT-M Futures
- **Backtesting Engine**: Full Backtrader integration with historical data
- **Trading Strategies**: Plugin-based strategy system with Smart Money Concepts (SMC)
- **Risk Management**: Configurable position sizing, stop-loss, and take-profit
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
