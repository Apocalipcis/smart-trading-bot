# Trading Bot API Documentation

## Overview

The Smart Trading Bot API provides a comprehensive RESTful interface for cryptocurrency trading on Binance Futures with simulation capabilities. The API follows REST principles and uses JSON for data exchange.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: Currently supports API key-based authentication for live trading
**Content-Type**: `application/json`

## API Endpoints

### Core Endpoints

#### Health & Status

##### GET `/status/health`
Get basic health status of the trading bot.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": 3600.5,
  "database_connected": true,
  "exchange_connected": true,
  "simulation_running": true,
  "trading_mode": "simulation"
}
```

##### GET `/status/health/detailed`
Get detailed health status including component status.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": 3600.5,
  "components": {
    "database": {
      "status": "healthy",
      "response_time": 0.002
    },
    "exchange": {
      "status": "healthy",
      "response_time": 0.150
    },
    "simulation_engine": {
      "status": "running",
      "portfolio_value": 10250.75
    }
  },
  "trading_mode": "simulation"
}
```

##### GET `/status/metrics`
Get system performance metrics.

**Response**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "metrics": {
    "api_requests_per_minute": 45,
    "average_response_time": 0.125,
    "memory_usage_mb": 256,
    "cpu_usage_percent": 12.5,
    "active_connections": 8
  }
}
```

#### Trading Pairs

##### GET `/pairs`
Get list of available trading pairs.

**Query Parameters**:
- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 50)

**Response**:
```json
{
  "items": [
    {
      "symbol": "BTCUSDT",
      "base_asset": "BTC",
      "quote_asset": "USDT",
      "status": "TRADING",
      "price_precision": 2,
      "quantity_precision": 3,
      "min_notional": 5.0,
      "tick_size": 0.01,
      "step_size": 0.001
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

##### GET `/pairs/{pair_id}`
Get specific trading pair information.

**Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "symbol": "BTCUSDT",
  "base_asset": "BTC",
  "quote_asset": "USDT",
  "strategy": "SMCSignalStrategy",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

##### POST `/pairs`
Add a new trading pair to the system.

**Request Body**:
```json
{
  "symbol": "ETHUSDT",
  "base_asset": "ETH",
  "quote_asset": "USDT",
  "strategy": "SMCSignalStrategy"
}
```

##### PUT `/pairs/{pair_id}`
Update an existing trading pair.

**Request Body**:
```json
{
  "symbol": "ETHUSDT",
  "base_asset": "ETH",
  "quote_asset": "USDT",
  "strategy": "SMCSignalStrategy",
  "is_active": true
}
```

##### DELETE `/pairs/{pair_id}`
Remove a trading pair from the system.

#### Trading Signals

##### GET `/signals`
Get trading signals with optional filtering.

**Query Parameters**:
- `pair` (string, optional): Filter by trading pair
- `strategy` (string, optional): Filter by strategy
- `side` (string, optional): Filter by side ('long' or 'short')
- `limit` (int, optional): Number of signals to return (default: 100)
- `page` (int, optional): Page number (default: 1)

**Response**:
```json
{
  "items": [
    {
      "id": "signal-123",
      "pair": "BTCUSDT",
      "strategy": "SMCSignalStrategy",
      "side": "long",
      "entry": 45000.0,
      "stop_loss": 44000.0,
      "take_profit": 47000.0,
      "confidence": 0.85,
      "timestamp": "2024-01-15T10:30:00Z",
      "metadata": {
        "trend": "bullish",
        "rsi": 45.0,
        "volume_ratio": 1.8
      }
    }
  ],
  "total": 1,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

##### GET `/signals/{signal_id}`
Get specific signal details.

**Response**:
```json
{
  "id": "signal-123",
  "pair": "BTCUSDT",
  "strategy": "SMCSignalStrategy",
  "side": "long",
  "entry": 45000.0,
  "stop_loss": 44000.0,
  "take_profit": 47000.0,
  "confidence": 0.85,
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "trend": "bullish",
    "rsi": 45.0,
    "volume_ratio": 1.8,
    "order_blocks": 3,
    "fair_value_gaps": 2
  }
}
```

##### GET `/signals/stream`
Stream real-time trading signals using Server-Sent Events (SSE).

**Response** (SSE format):
```
data: {"id": "signal-124", "pair": "BTCUSDT", "side": "short", "entry": 44800.0, "timestamp": "2024-01-15T10:31:00Z"}

data: {"id": "signal-125", "pair": "ETHUSDT", "side": "long", "entry": 3200.0, "timestamp": "2024-01-15T10:32:00Z"}
```

#### Backtesting

##### GET `/backtests`
Get list of backtest results.

**Query Parameters**:
- `pair` (string, optional): Filter by trading pair
- `strategy` (string, optional): Filter by strategy
- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 50)

**Response**:
```json
{
  "items": [
    {
      "id": "backtest-123",
      "pair": "BTCUSDT",
      "strategy": "SMCSignalStrategy",
      "timeframe": "1m",
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-15T00:00:00Z",
      "initial_capital": 10000.0,
      "final_capital": 12500.0,
      "total_return": 25.0,
      "win_rate": 0.68,
      "total_trades": 45,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

##### POST `/backtests`
Create a new backtest.

**Request Body**:
```json
{
  "pair": "BTCUSDT",
  "strategy": "SMCSignalStrategy",
  "timeframe": "1m",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-15T00:00:00Z",
  "initial_capital": 10000.0,
  "parameters": {
    "risk_per_trade": 0.02,
    "min_risk_reward": 3.0
  }
}
```

**Response**:
```json
{
  "id": "backtest-124",
  "status": "running",
  "progress": 0.0,
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

##### GET `/backtests/{backtest_id}`
Get detailed backtest results.

**Response**:
```json
{
  "id": "backtest-123",
  "pair": "BTCUSDT",
  "strategy": "SMCSignalStrategy",
  "timeframe": "1m",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-15T00:00:00Z",
  "status": "completed",
  "results": {
    "initial_capital": 10000.0,
    "final_capital": 12500.0,
    "total_return": 25.0,
    "sharpe_ratio": 1.85,
    "max_drawdown": -8.5,
    "win_rate": 0.68,
    "total_trades": 45,
    "winning_trades": 31,
    "losing_trades": 14,
    "average_win": 2.5,
    "average_loss": -1.2,
    "profit_factor": 2.1
  },
  "trades": [
    {
      "timestamp": "2024-01-01T01:00:00Z",
      "side": "long",
      "entry": 45000.0,
      "exit": 45500.0,
      "quantity": 0.1,
      "pnl": 50.0,
      "commission": 0.5
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

##### DELETE `/backtests/{backtest_id}`
Delete a backtest result.

##### DELETE `/backtests`
Delete all backtest results.

#### Orders (Live Trading Only)

##### GET `/orders`
Get list of orders (requires trading mode).

**Query Parameters**:
- `pair` (string, optional): Filter by trading pair
- `status` (string, optional): Filter by order status
- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 50)

**Response**:
```json
{
  "items": [
    {
      "id": "order-123",
      "pair": "BTCUSDT",
      "side": "buy",
      "order_type": "market",
      "quantity": 0.001,
      "price": 45000.0,
      "status": "filled",
      "filled_quantity": 0.001,
      "average_price": 45000.0,
      "commission": 0.045,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:05Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

##### POST `/orders`
Create a new order (requires trading mode).

**Request Body**:
```json
{
  "pair": "BTCUSDT",
  "side": "buy",
  "order_type": "market",
  "quantity": 0.001,
  "price": 45000.0,
  "stop_loss": 44000.0,
  "take_profit": 47000.0
}
```

**Response**:
```json
{
  "id": "order-124",
  "status": "pending",
  "message": "Order submitted successfully"
}
```

##### GET `/orders/{order_id}`
Get specific order details.

##### DELETE `/orders/{order_id}`
Cancel an order.

#### Settings

##### GET `/settings`
Get current application settings.

**Response**:
```json
{
  "trading_enabled": false,
  "order_confirmation_required": true,
  "max_open_positions": 5,
  "risk_per_trade": 2.0,
  "default_leverage": 1,
  "telegram_enabled": false,
  "max_risk_per_trade": 2.0,
  "min_risk_reward_ratio": 3.0,
  "debug_mode": false
}
```

##### PUT `/settings`
Update application settings.

**Request Body**:
```json
{
  "order_confirmation_required": false,
  "max_open_positions": 3,
  "risk_per_trade": 1.5
}
```

#### Notifications

##### POST `/notifications/test`
Send a test notification (if Telegram is configured).

**Request Body**:
```json
{
  "message": "Test notification from trading bot"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Test notification sent successfully"
}
```

### Simulation Endpoints

#### Simulation Status

##### GET `/simulation/status`
Get simulation engine status.

**Response**:
```json
{
  "running": true,
  "mode": "simulation",
  "portfolio_value": 10250.75,
  "positions_count": 2,
  "orders_count": 15,
  "stats": {
    "total_trades": 25,
    "winning_trades": 18,
    "losing_trades": 7,
    "win_rate": 0.72,
    "total_pnl": 250.75,
    "max_drawdown": -150.25
  }
}
```

##### POST `/simulation/start`
Start the simulation engine.

**Response**:
```json
{
  "success": true,
  "message": "Simulation engine started successfully"
}
```

##### POST `/simulation/stop`
Stop the simulation engine.

**Response**:
```json
{
  "success": true,
  "message": "Simulation engine stopped successfully"
}
```

##### POST `/simulation/reset`
Reset the simulation (clear all positions and history).

**Response**:
```json
{
  "success": true,
  "message": "Simulation reset successfully"
}
```

#### Simulation Portfolio

##### GET `/simulation/portfolio`
Get current portfolio information.

**Response**:
```json
{
  "total_value": 10250.75,
  "cash": 5000.0,
  "positions_value": 5250.75,
  "unrealized_pnl": 250.75,
  "realized_pnl": 0.0,
  "total_pnl": 250.75,
  "daily_pnl": 125.50,
  "daily_return": 1.24
}
```

##### GET `/simulation/positions`
Get open positions.

**Response**:
```json
{
  "positions": [
    {
      "pair": "BTCUSDT",
      "side": "long",
      "quantity": 0.1,
      "entry_price": 45000.0,
      "current_price": 45250.0,
      "unrealized_pnl": 250.0,
      "unrealized_pnl_percent": 5.56,
      "stop_loss": 44000.0,
      "take_profit": 47000.0,
      "opened_at": "2024-01-15T09:30:00Z"
    }
  ],
  "total_positions": 1
}
```

##### GET `/simulation/trades`
Get trade history.

**Query Parameters**:
- `pair` (string, optional): Filter by trading pair
- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 50)

**Response**:
```json
{
  "trades": [
    {
      "id": "trade-123",
      "pair": "BTCUSDT",
      "side": "buy",
      "quantity": 0.1,
      "entry_price": 45000.0,
      "exit_price": 45250.0,
      "pnl": 250.0,
      "commission": 4.5,
      "net_pnl": 245.5,
      "entry_time": "2024-01-15T09:30:00Z",
      "exit_time": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

##### GET `/simulation/performance`
Get performance metrics.

**Response**:
```json
{
  "total_return": 2.51,
  "sharpe_ratio": 1.85,
  "max_drawdown": -1.47,
  "win_rate": 0.72,
  "profit_factor": 2.1,
  "average_win": 125.0,
  "average_loss": -75.0,
  "total_trades": 25,
  "winning_trades": 18,
  "losing_trades": 7,
  "best_trade": 300.0,
  "worst_trade": -150.0
}
```

#### Simulation Admin

##### POST `/simulation/admin/trading/approve`
Approve live trading (admin only).

**Response**:
```json
{
  "success": true,
  "message": "Live trading approved successfully"
}
```

##### POST `/simulation/admin/trading/revoke`
Revoke live trading approval (admin only).

**Response**:
```json
{
  "success": true,
  "message": "Live trading approval revoked"
}
```

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "correlation_id": "req-123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

- `400` - Bad Request: Invalid request parameters
- `401` - Unauthorized: Authentication required
- `403` - Forbidden: Insufficient permissions
- `404` - Not Found: Resource not found
- `422` - Validation Error: Invalid data format
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Server error
- `503` - Service Unavailable: Service temporarily unavailable

### Trading-Specific Error Codes

- `TRADING_DISABLED` - Trading is not enabled
- `INSUFFICIENT_BALANCE` - Insufficient account balance
- `INVALID_ORDER` - Invalid order parameters
- `ORDER_NOT_FOUND` - Order not found
- `SIMULATION_ONLY` - Operation only available in simulation mode
- `LIVE_TRADING_NOT_APPROVED` - Live trading not approved

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **General endpoints**: 100 requests per minute
- **Trading endpoints**: 10 requests per minute
- **Simulation endpoints**: 50 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642234560
```

## WebSocket Support

### Real-time Data Streams

Connect to WebSocket endpoint for real-time data:

```
ws://localhost:8000/ws
```

### Available Streams

- **Price Updates**: `price.{symbol}`
- **Signal Updates**: `signals`
- **Portfolio Updates**: `portfolio`
- **Order Updates**: `orders`

### WebSocket Message Format

```json
{
  "type": "price_update",
  "symbol": "BTCUSDT",
  "data": {
    "bid": 45000.0,
    "ask": 45001.0,
    "last": 45000.5,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Authentication

### API Key Authentication

For live trading, API keys are required:

```
Authorization: Bearer YOUR_API_KEY
```

### Simulation Mode

No authentication required for simulation mode operations.

## Data Models

### Signal Model

```json
{
  "side": "long|short",
  "entry": 45000.0,
  "stop_loss": 44000.0,
  "take_profit": 47000.0,
  "confidence": 0.85,
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {}
}
```

### Order Model

```json
{
  "pair": "BTCUSDT",
  "side": "buy|sell",
  "order_type": "market|limit|stop",
  "quantity": 0.001,
  "price": 45000.0,
  "stop_loss": 44000.0,
  "take_profit": 47000.0
}
```

### Portfolio Model

```json
{
  "total_value": 10250.75,
  "cash": 5000.0,
  "positions_value": 5250.75,
  "unrealized_pnl": 250.75,
  "realized_pnl": 0.0
}
```

## SDK Examples

### Python SDK

```python
import requests

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your_api_key"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Get health status
response = requests.get(f"{BASE_URL}/status/health")
print(response.json())

# Get signals
response = requests.get(f"{BASE_URL}/signals?pair=BTCUSDT&limit=10")
signals = response.json()["items"]

# Create backtest
backtest_data = {
    "pair": "BTCUSDT",
    "strategy": "SMCSignalStrategy",
    "timeframe": "1m",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-15T00:00:00Z",
    "initial_capital": 10000.0
}

response = requests.post(f"{BASE_URL}/backtests", json=backtest_data, headers=headers)
backtest_id = response.json()["id"]
```

### JavaScript SDK

```javascript
const API_BASE = 'http://localhost:8000/api/v1';
const API_KEY = 'your_api_key';

const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
};

// Get portfolio
async function getPortfolio() {
    const response = await fetch(`${API_BASE}/simulation/portfolio`, { headers });
    return await response.json();
}

// Stream signals
function streamSignals() {
    const eventSource = new EventSource(`${API_BASE}/signals/stream`);
    
    eventSource.onmessage = function(event) {
        const signal = JSON.parse(event.data);
        console.log('New signal:', signal);
    };
}
```

## Best Practices

### Error Handling

Always check for errors in responses:

```python
response = requests.get(f"{BASE_URL}/signals")
if response.status_code == 200:
    data = response.json()
else:
    error = response.json()
    print(f"Error: {error['error']}")
```

### Rate Limiting

Implement exponential backoff for rate-limited requests:

```python
import time

def make_request_with_backoff(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)
        if response.status_code != 429:
            return response
        
        wait_time = 2 ** attempt
        time.sleep(wait_time)
    
    raise Exception("Max retries exceeded")
```

### WebSocket Connection

Handle WebSocket reconnection:

```javascript
function connectWebSocket() {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onclose = function() {
        console.log('WebSocket closed, reconnecting...');
        setTimeout(connectWebSocket, 1000);
    };
    
    return ws;
}
```

## Changelog

### v1.0.0
- Initial API implementation
- Complete simulation engine endpoints
- Real-time signal streaming
- Comprehensive backtesting API
- WebSocket support for real-time data
- Rate limiting and error handling
- Full documentation and examples
