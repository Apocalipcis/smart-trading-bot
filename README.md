# Smart Money Concepts (SMC) Signal Service

A comprehensive trading signal service that generates real-time and historical Smart Money Concepts (SMC) signals with local storage, backtesting capabilities, and a modern web interface.

## 🆕 Latest Updates (v0.1.0)

### ✅ **Import Issues Fixed**
- **Docker Dependencies**: Resolved missing `pydantic` package installation
- **Cache Manager**: Fixed `CacheManager` import error in storage module  
- **Trading State**: Added missing `execution_enabled` property
- **Import Chain**: All import dependencies now work correctly

### 🚀 **View-Only Mode Implemented**
- **Mock Binance Client**: Generates realistic test data without API keys
- **Mock SMC Engine**: Simulates SMC signal generation for testing
- **Mock Backtest Engine**: Provides backtesting functionality without live data
- **No API Keys Required**: System runs immediately after setup

### 🔧 **Current Status**
- **API Container**: ✅ Running on port 8000
- **Worker Container**: ✅ Running on port 8001  
- **Mock Data**: ✅ Generating every 30 seconds
- **Web Interface**: ✅ Fully functional
- **Import Errors**: ✅ All resolved

## 🚀 Features

- **Real-time Data**: WebSocket integration with Binance for live market data
- **SMC Signals**: Break of Structure (BOS), Change of Character (CHOCH), Fair Value Gaps (FVG), Sweeps
- **Multi-timeframe Support**: 1m, 5m, 15m, 30m, 1h, 4h, 1d
- **Local Storage**: Efficient Parquet-based data storage with in-memory caching
- **Backtesting Engine**: Historical strategy testing with comprehensive metrics
- **CSV Reports**: Detailed trade analysis exports
- **Volatility Scanner**: Market volatility ranking and analysis
- **Modern Web UI**: Responsive dashboard with HTMX for dynamic updates
- **REST API**: Full-featured API for integration and automation
- **Docker Support**: Easy deployment with docker-compose

## 🏗️ Architecture

### 🎭 **View-Only Mode (Default)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Mock Binance   │    │  Mock WebSocket │    │   FastAPI App   │
│   (Simulated)   │    │   (Test Data)   │    │   (Web + API)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Parquet Storage│
                    │  + In-Memory    │
                    │     Cache       │
                    └─────────────────┘
```

### 🔑 **Live Trading Mode (With API Keys)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Binance API   │    │  WebSocket WS   │    │   FastAPI App   │
│   (Historical)  │    │   (Real-time)   │    │   (Web + API)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Parquet Storage│
                    │  + In-Memory    │
                    │     Cache       │
                    └─────────────────┘
```

## 📋 Requirements

- Python 3.11+
- Docker & Docker Compose
- Binance API credentials (for live data)

## 🚀 Quick Start

### 🎯 **View-Only Mode (Recommended for Testing)**

The system now runs in **view-only mode** by default, generating realistic mock data without requiring Binance API keys:

```bash
# Clone and setup
git clone <repository-url>
cd smart-trading-bot

# Start services immediately (no configuration needed)
docker compose up --build
```

**What you get:**
- ✅ **Mock market data** for BTCUSDT, ETHUSDT, BNBUSDT
- ✅ **SMC signals** generated every 30 seconds
- ✅ **Full backtesting** with simulated data
- ✅ **Web dashboard** fully functional
- ✅ **API endpoints** working without authentication

### 🔑 **Live Trading Mode (Optional)**

For live trading with real data, configure your Binance API credentials:

### 1. Clone and Setup

```bash
git clone <repository-url>
cd smart-trading-bot
cp env.example .env
```

### 2. Configure Environment

Edit `.env` file with your Binance API credentials:

```bash
# Binance API Configuration
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
BINANCE_TESTNET=false

# Security
SHARED_SECRET=your_shared_secret_here
```

### 3. Start Services

```bash
# Start both API and WebSocket worker
docker compose up --build

# Or start services individually
docker compose up api      # FastAPI service on port 8000
docker compose up worker   # WebSocket worker on port 8001
```

### 4. Verify Installation

- **API Health**: http://localhost:8000/health
- **Web Dashboard**: http://localhost:8000/web/
- **API Documentation**: http://localhost:8000/docs
- **Backtest Interface**: http://localhost:8000/web/backtest

## 📊 Data Sources

### 🎭 **Mock Data (View-Only Mode)**
- **Realistic Simulation**: Generates OHLCV data similar to real market conditions
- **Update Frequency**: New candles every 30 seconds
- **Supported Pairs**: BTCUSDT, ETHUSDT, BNBUSDT
- **Timeframes**: 1m, 5m, 15m (configurable)
- **No API Keys**: Works immediately after startup

### 📈 **Historical Data (Live Mode)**
- **Binance REST API**: Historical kline data backfill
- **Timeframes**: 1m, 5m, 15m, 30m, 1h, 4h, 1d
- **Storage**: Local Parquet files in `./data/` directory

### ⚡ **Real-time Data (Live Mode)**
- **Binance WebSocket**: Live kline streaming
- **Supported Pairs**: BTCUSDT, ETHUSDT, BNBUSDT (configurable)
- **Update Frequency**: Real-time as candles close

## 🔧 API Endpoints

### Core Endpoints
- `GET /health` - Service health check
- `GET /api/v1/pairs/` - Available trading pairs
- `GET /api/v1/candles/` - Historical candle data
- `GET /api/v1/signals/` - SMC trading signals

### Advanced Features
- `GET /api/v1/backtest/` - Run strategy backtests
- `GET /api/v1/scan/volatility` - Volatility analysis
- `GET /api/v1/signals/stats/summary` - Signal statistics

### Example API Usage

```bash
# Get latest candles for BTCUSDT 15m
curl "http://localhost:8000/api/v1/candles/?symbol=BTCUSDT&timeframe=15m&limit=100"

# Run backtest for ETHUSDT 1h
curl "http://localhost:8000/api/v1/backtest/?symbol=ETHUSDT&tf=1h&from_date=2024-01-01&to_date=2024-01-31"

# Get volatility ranking
curl "http://localhost:8000/api/v1/scan/volatility?tf=15m&top=20"
```

## 🧪 Backtesting

### Features
- **Strategy Simulation**: Breakout strategy with configurable parameters
- **Risk Management**: Stop-loss and take-profit automation
- **Performance Metrics**: Win rate, profit factor, R-multiple, drawdown
- **CSV Export**: Detailed trade-by-trade analysis

### Metrics Calculated
- Total trades, win rate, profit factor
- Average R-multiple, expectancy
- Maximum drawdown, Sharpe-like ratio
- Time in market, MAE/MFE analysis

## 📈 Web Interface

### Dashboard
- Real-time signal monitoring
- Market overview and statistics
- Volatility scanner with timeframe selection
- Available pairs and timeframes

### Backtest Interface
- Strategy parameter configuration
- Interactive results display
- Performance metrics visualization
- CSV report download

## 🗄️ Data Storage

### Structure
```
data/
├── candles/          # OHLCV data by symbol/timeframe
├── signals/          # SMC signals by symbol/timeframe
└── backtests/        # Backtest results

reports/              # CSV exports
├── {symbol}/
└── {timeframe}/
```

### Storage Format
- **Parquet**: Efficient columnar storage for time-series data
- **Compression**: Snappy compression for optimal size/performance
- **Partitioning**: Organized by symbol and timeframe
- **Caching**: In-memory LRU cache with TTL

## 🔌 Configuration

### Environment Variables
```bash
# Data Configuration
DATA_DIR=./data
REPORTS_DIR=./reports
CACHE_TTL=300

# WebSocket Configuration
WS_RECONNECT_DELAY=5
WS_MAX_RECONNECT_ATTEMPTS=10

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
WORKER_HOST=0.0.0.0
WORKER_PORT=8001

# Indicators
INDICATORS=BOS,CHOCH,FVG,SWEEP
TIMEFRAMES=1m,5m,15m,30m,1h,4h,1d
```

### Customization
- **Symbols**: Modify `WebSocketWorker.symbols` in `app/workers/websocket_worker.py`
- **Timeframes**: Update `TIMEFRAMES` in `.env`
- **Indicators**: Configure `INDICATORS` in `.env`

## 🚀 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements.txt[dev]

# Run services
python -m app.main          # API service
python -m app.workers.websocket_worker  # WebSocket worker
```

### Code Quality
```bash
# Formatting
black app/
ruff check app/

# Type checking
mypy app/

# Testing
pytest tests/
```

### Project Structure
```
smart-trading-bot/
├── app/
│   ├── api/              # REST API endpoints
│   ├── models/           # Pydantic data models
│   ├── services/         # Business logic
│   │   ├── binance_client.py    # Mock Binance client (view-only)
│   │   ├── smc_engine.py        # Mock SMC signal engine
│   │   └── backtest_engine.py   # Mock backtesting engine
│   ├── storage/          # Data persistence
│   ├── web/              # Web interface
│   └── workers/          # Background workers
├── data/                 # Parquet storage
├── reports/              # CSV exports
├── tests/                # Test suite
├── docker-compose.yml    # Docker configuration
└── requirements.txt      # Python dependencies
```

## 🔒 Security

### API Security
- **Rate Limiting**: Configurable request limits
- **Shared Secret**: X-Shared-Secret header validation
- **CORS**: Configurable cross-origin policies

### Data Security
- **Local Storage**: No external database dependencies
- **API Keys**: Secure environment variable storage
- **Access Control**: Future-ready permission system

## 📊 Monitoring

### Health Checks
- **Service Health**: `/health` endpoint
- **Cache Status**: Built-in cache monitoring
- **Storage Status**: Parquet file integrity checks

### Logging
- **Structured Logging**: JSON-like format
- **Log Levels**: Configurable verbosity
- **Error Tracking**: Comprehensive error handling

## 🚧 Future Enhancements

### Planned Features
- **SMC Indicators**: Advanced BOS/CHOCH/FVG detection
- **Execution Engine**: Order management and execution
- **Risk Management**: Position sizing and portfolio management
- **Machine Learning**: Signal prediction and optimization
- **Multi-exchange**: Support for additional exchanges

### Execution Foundation
- **Order Management**: Order lifecycle tracking
- **Position Tracking**: Real-time P&L monitoring
- **Risk Controls**: Maximum position limits
- **Audit Logging**: Complete trade history

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure code quality (black, ruff, mypy)
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. It is not financial advice. Trading cryptocurrencies involves substantial risk and may result in the loss of your invested capital. Always do your own research and consider consulting with a financial advisor before making investment decisions.

## 🆘 Support

### 🐛 **Troubleshooting**

#### **Import Errors (Fixed)**
If you encounter import errors, they have been resolved in v0.1.0:

```bash
# ✅ Fixed: Missing pydantic dependency
# Solution: Docker image now includes all required packages

# ✅ Fixed: CacheManager import error  
# Solution: Added CacheManager alias in cache_manager.py

# ✅ Fixed: execution_enabled attribute error
# Solution: Added missing property in TradingState class
```

#### **Common Issues**
- **Port already in use**: Change ports in `docker-compose.yml`
- **Permission denied**: Ensure Docker has proper permissions
- **Container won't start**: Check logs with `docker-compose logs`

### **Issues**: GitHub Issues for bug reports and feature requests

---

**Built with ❤️ for the trading community**
