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
- Python 3.11+
- Git

### Setup
```bash
# Clone repository
git clone <repository-url>
cd smart-trading-bot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Trading Configuration
TRADING_ENABLED=false
ORDER_CONFIRMATION_REQUIRED=true
MAX_OPEN_POSITIONS=5
MAX_RISK_PER_TRADE=2.0
MIN_RISK_REWARD_RATIO=3.0

# Binance API (required for trading)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# Telegram Notifications (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLED=false

# System Configuration
DEBUG_MODE=false
ENVIRONMENT=development
DATA_DIR=/data
DB_PATH=/data/app.db

# Exchange URLs
EXCHANGE=binance_futures
WS_URL=wss://fstream.binance.com/ws
REST_URL=https://fapi.binance.com
```

## 🚀 Running the Application

### Start the API Server
```bash
# Development mode with auto-reload
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Access the API
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/status/health

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=src tests/
```

## 📊 API Endpoints

### Core Endpoints
- `GET /` - Root endpoint
- `GET /api/v1` - API information
- `GET /docs` - Interactive documentation

### Trading Pairs
- `GET /api/v1/pairs` - List trading pairs
- `POST /api/v1/pairs` - Create new pair
- `PUT /api/v1/pairs/{symbol}` - Update pair
- `DELETE /api/v1/pairs/{symbol}` - Delete pair

### Signals
- `GET /api/v1/signals` - List signals
- `POST /api/v1/signals` - Create signal
- `GET /api/v1/signals/stream/sse` - Real-time streaming

### Backtests
- `GET /api/v1/backtests` - List backtest results
- `POST /api/v1/backtests` - Run new backtest
- `GET /api/v1/backtests/{id}/detailed` - Detailed results

### Orders (Trading Mode Only)
- `GET /api/v1/orders` - List orders
- `POST /api/v1/orders` - Create order
- `PUT /api/v1/orders/{id}/cancel` - Cancel order

### Settings
- `GET /api/v1/settings` - Get settings
- `PUT /api/v1/settings` - Update settings
- `POST /api/v1/settings/trading/toggle` - Toggle trading mode

### System Status
- `GET /api/v1/status/health` - Health check
- `GET /api/v1/status/metrics` - System metrics
- `GET /api/v1/status/info` - System information

### Notifications
- `POST /api/v1/notifications/test` - Test Telegram
- `POST /api/v1/notifications/signal` - Signal notification
- `POST /api/v1/notifications/backtest` - Backtest notification

## 🔒 Security Features

- **Environment Variables**: No hardcoded secrets
- **Trading Mode Control**: API key validation required
- **Rate Limiting**: Built-in request throttling
- **Input Validation**: Pydantic model validation
- **Structured Logging**: No sensitive data in logs

## 📈 Trading Features

### Risk Management
- Configurable position sizing based on account risk
- Minimum risk-reward ratio enforcement (≥3:1)
- Maximum open positions limit
- Stop-loss and take-profit automation

### Strategy System
- Plugin-based architecture
- Smart Money Concepts (SMC) baseline strategy
- Customizable parameters
- Strategy versioning

### Data Integrity
- UTC timestamp enforcement
- No look-ahead bias
- Candle data validation
- WebSocket reconnection handling

## 🐳 Docker Support

```bash
# Build image
docker build -t smart-trading-bot .

# Run container
docker run -p 8000:8000 -v $(pwd)/data:/data smart-trading-bot

# With docker-compose
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies involves substantial risk of loss and is not suitable for all investors. The authors are not responsible for any financial losses incurred through the use of this software.

## 🆘 Support

- **Issues**: Create a GitHub issue
- **Documentation**: Check the `/docs` endpoint
- **Community**: Join our Discord/Telegram channels

---

**Built with ❤️ using FastAPI, Backtrader, and modern Python practices**
