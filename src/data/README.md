# Data Layer

The data layer provides comprehensive data handling for Binance USDT-M Futures, including REST API access, WebSocket streaming, and Backtrader integration.

## Components

### 1. BinanceClient (`binance_client.py`)

**Purpose**: HTTPX-based REST client and WebSocket connection manager for Binance Futures.

**Features**:
- Async REST API calls with automatic retries
- WebSocket connection management
- Support for klines, trades, and book ticker data
- Proper error handling and timeout management

**Usage**:
```python
from src.data.binance_client import BinanceClient, BinanceConfig

config = BinanceConfig(
    rest_url="https://fapi.binance.com",
    ws_url="wss://fstream.binance.com"
)

async with BinanceClient(config) as client:
    # Get exchange info
    exchange_info = await client.get_exchange_info()
    
    # Get recent klines
    klines = await client.get_klines("BTCUSDT", "1m", limit=100)
    
    # Get book ticker
    ticker = await client.get_book_ticker("BTCUSDT")
```

### 2. BinanceValidator (`validators.py`)

**Purpose**: Validates exchange rules and constraints for orders and data.

**Features**:
- Price and quantity validation against tick/step sizes
- Minimum notional value checks
- Price and quantity normalization
- Support for all Binance filter types

**Usage**:
```python
from src.data.validators import BinanceValidator

validator = BinanceValidator()
validator.set_symbol_info('BTCUSDT', exchange_info)

# Validate order parameters
valid, msg = validator.validate_order('BTCUSDT', 50000.00, 1.000)

# Normalize prices to valid tick sizes
normalized_price = validator.normalize_price('BTCUSDT', 50000.005)
```

### 3. RateLimiter (`rate_limit.py`)

**Purpose**: Manages API rate limits with token bucket algorithm and retry logic.

**Features**:
- Token bucket rate limiting per request type
- Exponential backoff with jitter for retries
- Idempotency key support
- Automatic cleanup of expired keys

**Usage**:
```python
from src.data.rate_limit import RateLimiter, RateLimitConfig, RequestType

config = RateLimitConfig(
    requests_per_second=10,
    burst_size=20,
    retry_attempts=3
)

rate_limiter = RateLimiter(config)
await rate_limiter.start()

# Execute with rate limiting
result = await rate_limiter.execute_with_retry(
    my_function,
    RequestType.REST,
    idempotency_key="unique_key"
)
```

### 4. WebSocketStreamManager (`stream.py`)

**Purpose**: Manages live WebSocket streams with auto-reconnect and resync capabilities.

**Features**:
- Automatic reconnection with exponential backoff
- Sequence number tracking and gap detection
- REST API resync for missing data
- Event deduplication and handler management
- Heartbeat monitoring

**Usage**:
```python
from src.data.stream import WebSocketStreamManager, StreamConfig

config = StreamConfig(
    max_reconnect_attempts=10,
    base_reconnect_delay=1.0
)

stream_manager = WebSocketStreamManager(config, binance_client)
await stream_manager.start()

# Add event handlers
stream_manager.add_handler("btcusdt@kline_1m", my_kline_handler)
stream_manager.add_handler("btcusdt@trade", my_trade_handler)
```

### 5. BinanceDataFeed (`feed.py`)

**Purpose**: Custom Backtrader data feed supporting both offline and live modes.

**Features**:
- **Offline Mode**: Reads from Parquet files in `/data/candles/`
- **Live Mode**: Consumes from WebSocket streams
- Strict UTC timestamp handling
- No look-ahead bias protection
- Data integrity validation
- Automatic column mapping

**Usage**:
```python
import backtrader as bt
from src.data.feed import BinanceDataFeed

# Offline mode
feed = BinanceDataFeed(
    symbol='BTCUSDT',
    interval='1m',
    data_dir='/data',
    live=False
)

# Live mode
feed = BinanceDataFeed(
    symbol='BTCUSDT',
    interval='1m',
    data_dir='/data',
    live=True,
    stream_manager=stream_manager
)

# Add to Cerebro
cerebro = bt.Cerebro()
cerebro.adddata(feed)
```

## Data Storage Structure

The data layer expects the following directory structure:

```
/data/
├── candles/
│   └── binance_futures/
│       ├── BTCUSDT/
│       │   ├── 1m.parquet
│       │   ├── 5m.parquet
│       │   └── 1h.parquet
│       └── ETHUSDT/
│           └── 1m.parquet
└── backtests/
    └── 2024-01-15/
        └── BTCUSDT_smc_1m.json
```

## Configuration

All configuration is handled through environment variables:

```bash
# Exchange configuration
EXCHANGE=binance_futures
WS_URL=wss://fstream.binance.com
REST_URL=https://fapi.binance.com

# Data storage
DATA_DIR=/data
DB_PATH=/data/app.db

# API keys (for trading mode)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_data_layer.py

# Run with coverage
pytest --cov=src tests/
```

## Demo

Run the demonstration script:

```bash
python examples/data_layer_demo.py
```

## Integration with Backtrader

The `BinanceDataFeed` seamlessly integrates with Backtrader strategies:

```python
import backtrader as bt
from src.data.feed import BinanceDataFeed

class MyStrategy(bt.Strategy):
    def next(self):
        # Access current data
        current_price = self.data.close[0]
        current_volume = self.data.volume[0]
        
        # Strategy logic here
        if current_price > self.data.close[-1]:
            self.buy()

# Setup
cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)

# Add data feed
feed = BinanceDataFeed(
    symbol='BTCUSDT',
    interval='1m',
    data_dir='/data',
    live=False
)
cerebro.adddata(feed)

# Run backtest
cerebro.run()
```

## Performance Considerations

- **Signal Latency**: Live mode provides ≤1s latency from WebSocket events
- **Memory Usage**: Live mode keeps last 1000 candles in memory
- **File I/O**: Offline mode uses efficient Parquet format for historical data
- **Rate Limiting**: Automatic API rate limit compliance with configurable thresholds

## Error Handling

All components include comprehensive error handling:

- **Network Errors**: Automatic retries with exponential backoff
- **Data Validation**: Integrity checks for gaps, duplicates, and anomalies
- **WebSocket Recovery**: Automatic reconnection and data resync
- **Graceful Degradation**: Fallback to REST API when WebSocket fails
