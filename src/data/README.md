# Data Layer Package

A comprehensive data layer for the Smart Trading Bot that provides real-time and historical data from Binance Futures with robust error handling, rate limiting, and data validation.

## 🚀 Quick Start

### What This Package Does
- **Binance Integration**: REST API and WebSocket connections to Binance Futures
- **Real-time Data**: Live price feeds via WebSocket streaming
- **Historical Data**: Historical candle data download and storage
- **Data Validation**: Exchange rules and constraints enforcement
- **Rate Limiting**: API rate limit management and retry logic
- **WebSocket Recovery**: Auto-reconnect and data resynchronization

### Run the Demo (5 minutes)
```bash
# From project root
cd examples
python data_layer_demo.py
```

You should see:
- Exchange information retrieval
- Historical data download
- Real-time price streaming
- Data validation examples
- Rate limiting demonstrations

## 📦 Installation & Setup

### Dependencies
```bash
pip install python-binance websockets httpx pandas pyarrow
```

### Environment Variables
Create a `.env` file in the project root:

```env
# Binance API Configuration
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here

# WebSocket Configuration
WS_URL=wss://fstream.binance.com/ws
REST_URL=https://fapi.binance.com

# Data Storage
DATA_DIR=./data
CANDLES_DIR=./data/candles
```

## 🎯 Basic Usage

### Binance Client

```python
from src.data.binance_client import BinanceClient

# Create client instance
client = BinanceClient()

# Get exchange information
exchange_info = await client.get_exchange_info()
print(f"Exchange: {exchange_info['exchangeName']}")

# Get symbol information
btc_info = await client.get_symbol_info('BTCUSDT')
print(f"BTCUSDT tick size: {btc_info['tickSize']}")
```

### WebSocket Streaming

```python
from src.data.stream import BinanceWebSocketStream

# Create stream instance
stream = BinanceWebSocketStream(['btcusdt@kline_1m'])

# Start streaming
async def handle_message(msg):
    print(f"Received: {msg}")

await stream.start(handle_message)
```

### Data Feed

```python
from src.data.feed import DataFeed

# Create data feed
feed = DataFeed(['BTCUSDT'], ['1m', '5m', '1h'])

# Get latest data
latest_data = await feed.get_latest_data('BTCUSDT', '1m')
print(f"Latest BTC price: {latest_data['close']}")
```

## 🛠️ Core Components

### 1. BinanceClient

The main client for interacting with Binance Futures REST API:

```python
from src.data.binance_client import BinanceClient

class BinanceClient:
    """Binance Futures REST API client"""
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information and trading rules"""
        
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get specific symbol information"""
        
    async def get_klines(self, symbol: str, interval: str, 
                         start_time: Optional[int] = None,
                         end_time: Optional[int] = None,
                         limit: int = 1000) -> List[List[Any]]:
        """Get historical kline/candlestick data"""
        
    async def get_ticker_24hr(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker price change statistics"""
```

### 2. WebSocket Stream

Real-time data streaming via WebSocket:

```python
from src.data.stream import BinanceWebSocketStream

class BinanceWebSocketStream:
    """WebSocket stream for real-time data"""
    
    async def start(self, message_handler: Callable) -> None:
        """Start WebSocket connection and streaming"""
        
    async def stop(self) -> None:
        """Stop WebSocket connection"""
        
    async def subscribe(self, streams: List[str]) -> None:
        """Subscribe to specific data streams"""
        
    async def unsubscribe(self, streams: List[str]) -> None:
        """Unsubscribe from data streams"""
```

### 3. Data Feed

Unified interface for both real-time and historical data:

```python
from src.data.feed import DataFeed

class DataFeed:
    """Unified data feed for real-time and historical data"""
    
    async def get_latest_data(self, symbol: str, interval: str) -> Dict[str, Any]:
        """Get latest data point for symbol and interval"""
        
    async def get_historical_data(self, symbol: str, interval: str,
                                 start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """Get historical data for symbol and interval"""
        
    async def subscribe_to_updates(self, symbol: str, interval: str,
                                  callback: Callable) -> None:
        """Subscribe to real-time updates for symbol and interval"""
```

### 4. Data Validators

Exchange rules and data validation:

```python
from src.data.validators import DataValidator

class DataValidator:
    """Validate data according to exchange rules"""
    
    def validate_price(self, symbol: str, price: float) -> bool:
        """Validate price against tick size and price precision"""
        
    def validate_quantity(self, symbol: str, quantity: float) -> bool:
        """Validate quantity against step size and quantity precision"""
        
    def validate_order(self, symbol: str, side: str, 
                      quantity: float, price: float) -> bool:
        """Validate complete order parameters"""
```

### 5. Rate Limiter

API rate limit management:

```python
from src.data.rate_limit import RateLimiter

class RateLimiter:
    """Manage API rate limits and request throttling"""
    
    async def acquire(self, endpoint: str) -> None:
        """Acquire permission to make API request"""
        
    async def release(self, endpoint: str) -> None:
        """Release rate limit slot after request completion"""
        
    def get_remaining_requests(self, endpoint: str) -> int:
        """Get remaining requests for endpoint"""
```

## 📊 Data Formats

### Kline/Candlestick Data

```python
# Raw kline data from Binance
[
    1499040000000,      # Open time
    "0.01634790",       # Open
    "0.80000000",       # High
    "0.01575800",       # Low
    "0.01577100",       # Close
    "148976.11427815",  # Volume
    1499644799999,      # Close time
    "2434.19055334",    # Quote asset volume
    308,                # Number of trades
    "1756.87402397",    # Taker buy base asset volume
    "28.46694368"       # Taker buy quote asset volume
]

# Processed candle data
{
    'timestamp': datetime(2024, 1, 1, 0, 0),
    'open': 0.01634790,
    'high': 0.80000000,
    'low': 0.01575800,
    'close': 0.01577100,
    'volume': 148976.11427815,
    'quote_volume': 2434.19055334,
    'trades': 308,
    'taker_buy_volume': 1756.87402397,
    'taker_buy_quote_volume': 28.46694368
}
```

### WebSocket Messages

```python
# Kline/Candlestick stream
{
    "e": "kline",     # Event type
    "E": 123456789,   # Event time
    "s": "BTCUSDT",   # Symbol
    "k": {
        "t": 123400000,  # Kline start time
        "T": 123460000,  # Kline close time
        "s": "BTCUSDT",  # Symbol
        "i": "1m",       # Interval
        "f": 100,        # First trade ID
        "L": 200,        # Last trade ID
        "o": "0.0010",   # Open price
        "c": "0.0020",   # Close price
        "h": "0.0025",   # High price
        "l": "0.0015",   # Low price
        "v": "1000",     # Base asset volume
        "n": 100,        # Number of trades
        "x": false,      # Is this kline closed?
        "q": "1.0000",   # Quote asset volume
        "V": "500",      # Taker buy base asset volume
        "Q": "0.500"     # Taker buy quote asset volume
    }
}
```

## 🔧 Configuration

### Exchange Configuration

```python
from src.data.config import ExchangeConfig

config = ExchangeConfig(
    rest_url="https://fapi.binance.com",
    ws_url="wss://fstream.binance.com/ws",
    api_key="your_api_key",
    secret_key="your_secret_key",
    testnet=False
)
```

### Data Storage Configuration

```python
from src.data.config import DataConfig

data_config = DataConfig(
    data_dir="./data",
    candles_dir="./data/candles",
    max_file_size=100 * 1024 * 1024,  # 100MB
    compression="snappy"
)
```

### WebSocket Configuration

```python
from src.data.config import WebSocketConfig

ws_config = WebSocketConfig(
    ping_interval=30,
    ping_timeout=10,
    close_timeout=10,
    max_message_size=1024 * 1024,  # 1MB
    auto_reconnect=True,
    reconnect_delay=5
)
```

## 🚨 Error Handling

### Common Errors

#### 1. Rate Limit Exceeded
```python
try:
    data = await client.get_klines('BTCUSDT', '1m')
except RateLimitExceeded:
    # Wait for rate limit reset
    await asyncio.sleep(60)
    data = await client.get_klines('BTCUSDT', '1m')
```

#### 2. WebSocket Connection Lost
```python
try:
    await stream.start(handle_message)
except WebSocketConnectionError:
    # Auto-reconnect handled by stream
    print("WebSocket reconnecting...")
```

#### 3. Invalid Symbol
```python
try:
    info = await client.get_symbol_info('INVALID')
except InvalidSymbolError as e:
    print(f"Invalid symbol: {e}")
```

### Retry Logic

```python
from src.data.retry import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1)
async def get_data_with_retry():
    return await client.get_klines('BTCUSDT', '1m')
```

## 📈 Performance Optimization

### Data Caching

```python
from src.data.cache import DataCache

cache = DataCache(max_size=1000)

# Cache frequently accessed data
cached_data = cache.get('BTCUSDT_1m')
if cached_data is None:
    cached_data = await client.get_klines('BTCUSDT', '1m')
    cache.set('BTCUSDT_1m', cached_data)
```

### Batch Processing

```python
# Process multiple symbols at once
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
tasks = [client.get_symbol_info(symbol) for symbol in symbols]
results = await asyncio.gather(*tasks)
```

### Memory Management

```python
# Use generators for large datasets
async def get_large_dataset(symbol: str, start_time: int, end_time: int):
    async for batch in client.get_klines_batched(symbol, '1m', start_time, end_time):
        yield batch
```

## 🧪 Testing

### Unit Tests

```bash
# Run data layer tests
pytest tests/test_data/ -v

# Run specific test file
pytest tests/test_data/test_binance_client.py -v

# Run with coverage
pytest tests/test_data/ --cov=src.data
```

### Integration Tests

```bash
# Run integration tests (requires network)
pytest tests/test_data/ -m integration

# Test with real Binance API
pytest tests/test_data/ --env=live
```

### Mock Testing

```python
from unittest.mock import AsyncMock, patch

async def test_binance_client():
    with patch('src.data.binance_client.httpx.AsyncClient') as mock_client:
        mock_client.return_value.get.return_value.json = AsyncMock(
            return_value={'exchangeName': 'Binance Futures'}
        )
        
        client = BinanceClient()
        info = await client.get_exchange_info()
        assert info['exchangeName'] == 'Binance Futures'
```

## 🔒 Security

### API Key Management

- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate keys regularly
- Use read-only keys for testing

### Data Validation

- Validate all incoming data
- Sanitize user inputs
- Check data integrity
- Log suspicious activities

### Rate Limiting

- Respect exchange rate limits
- Implement exponential backoff
- Monitor API usage
- Alert on rate limit violations

## 📊 Monitoring

### Health Checks

```python
from src.data.monitoring import DataLayerHealth

health = DataLayerHealth()

# Check data layer health
status = await health.check_health()
print(f"Data layer status: {status}")

# Get performance metrics
metrics = await health.get_metrics()
print(f"API response time: {metrics['avg_response_time']}ms")
```

### Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Log data operations
logger.info("Downloading historical data", 
           symbol="BTCUSDT", 
           interval="1h", 
           start_time=start_time)

# Log errors
logger.error("Failed to connect to WebSocket", 
            error=str(e), 
            retry_count=retry_count)
```

## 🤝 Contributing

### Adding New Data Sources

1. Create new client class inheriting from `BaseDataClient`
2. Implement required methods
3. Add configuration options
4. Write comprehensive tests
5. Update documentation

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

*Remember: Always validate data and handle errors gracefully in production environments.*
