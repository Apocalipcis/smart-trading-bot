# API Package

A comprehensive FastAPI application for the Smart Trading Bot that provides RESTful API endpoints, WebSocket streaming, and Server-Sent Events (SSE) for real-time data and control.

## 🚀 Quick Start

### What This Package Does
- **RESTful API**: Complete HTTP API for all bot operations
- **WebSocket Streaming**: Real-time data streaming for live updates
- **Server-Sent Events**: SSE endpoints for real-time notifications
- **OpenAPI Documentation**: Interactive API documentation with Swagger UI
- **Authentication & Security**: JWT-based authentication and rate limiting

### Start the API Server
```bash
# From project root
python -m src.startup

# Or using uvicorn directly
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📦 Installation & Setup

### Dependencies
```bash
pip install fastapi uvicorn pydantic python-multipart
```

### Environment Variables
Create a `.env` file in the project root:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_RELOAD=true

# Security
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20
```

## 🎯 Basic Usage

### Health Check

```bash
# Basic health check
curl http://localhost:8000/api/v1/status/health

# Detailed health check
curl http://localhost:8000/api/v1/status/health/detailed

# System metrics
curl http://localhost:8000/api/v1/status/metrics
```

### Trading Pairs

```bash
# Get all trading pairs
curl http://localhost:8000/api/v1/pairs/

# Get specific pair
curl http://localhost:8000/api/v1/pairs/BTCUSDT

# Add new pair
curl -X POST "http://localhost:8000/api/v1/pairs/" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "ETHUSDT", "enabled": true}'
```

### Trading Signals

```bash
# Get all signals
curl http://localhost:8000/api/v1/signals/

# Get signals for specific pair
curl http://localhost:8000/api/v1/signals/?symbol=BTCUSDT

# Stream signals (SSE)
curl -N http://localhost:8000/api/v1/signals/stream
```

## 🛠️ Core Components

### 1. Main Application

The FastAPI application entry point:

```python
from src.api.main import app

# FastAPI application instance
app = FastAPI(
    title="Smart Trading Bot API",
    description="Professional trading bot API with real-time data and control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

### 2. API Routers

Organized endpoint groups:

```python
from src.api.routers import pairs, signals, backtests, simulation, status

# Include routers
app.include_router(pairs.router, prefix="/api/v1/pairs", tags=["pairs"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(backtests.router, prefix="/api/v1/backtests", tags=["backtests"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])
app.include_router(status.router, prefix="/api/v1/status", tags=["status"])
```

### 3. Pydantic Schemas

Data validation and serialization:

```python
from src.api.schemas import Pair, Signal, BacktestRequest, BacktestResult

@dataclass
class Pair:
    """Trading pair information"""
    symbol: str
    enabled: bool
    base_asset: str
    quote_asset: str
    min_notional: float
    price_precision: int
    quantity_precision: int

@dataclass
class Signal:
    """Trading signal"""
    id: str
    symbol: str
    side: str  # 'long' or 'short'
    entry: float
    stop_loss: float
    take_profit: float
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any]
```

### 4. Dependencies

Dependency injection and shared services:

```python
from src.api.dependencies import get_data_service, get_strategy_service

async def get_data_service() -> DataService:
    """Get data service instance"""
    return DataService()

async def get_strategy_service() -> StrategyService:
    """Get strategy service instance"""
    return StrategyService()

# Use in endpoints
@router.get("/pairs/")
async def get_pairs(
    data_service: DataService = Depends(get_data_service)
) -> List[Pair]:
    """Get all trading pairs"""
    return await data_service.get_pairs()
```

### 5. Middleware

Request processing and logging:

```python
from src.api.middleware import LoggingMiddleware, CorrelationMiddleware

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

## 📊 API Endpoints

### Trading Pairs

```python
# GET /api/v1/pairs/
async def get_pairs() -> List[Pair]:
    """Get all trading pairs"""

# GET /api/v1/pairs/{symbol}
async def get_pair(symbol: str) -> Pair:
    """Get specific trading pair"""

# POST /api/v1/pairs/
async def create_pair(pair: PairCreate) -> Pair:
    """Create new trading pair"""

# PUT /api/v1/pairs/{symbol}
async def update_pair(symbol: str, pair: PairUpdate) -> Pair:
    """Update trading pair"""

# DELETE /api/v1/pairs/{symbol}
async def delete_pair(symbol: str) -> bool:
    """Delete trading pair"""
```

### Trading Signals

```python
# GET /api/v1/signals/
async def get_signals(
    symbol: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Signal]:
    """Get trading signals"""

# GET /api/v1/signals/{signal_id}
async def get_signal(signal_id: str) -> Signal:
    """Get specific signal"""

# GET /api/v1/signals/stream
async def stream_signals() -> EventSourceResponse:
    """Stream signals via Server-Sent Events"""

# POST /api/v1/signals/
async def create_signal(signal: SignalCreate) -> Signal:
    """Create new signal"""
```

### Backtesting

```python
# POST /api/v1/backtests/
async def create_backtest(request: BacktestRequest) -> BacktestResult:
    """Create and run backtest"""

# GET /api/v1/backtests/
async def get_backtests(
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[BacktestResult]:
    """Get backtest results"""

# GET /api/v1/backtests/{backtest_id}
async def get_backtest(backtest_id: str) -> BacktestResult:
    """Get specific backtest result"""

# DELETE /api/v1/backtests/{backtest_id}
async def delete_backtest(backtest_id: str) -> bool:
    """Delete backtest result"""

# DELETE /api/v1/backtests/
async def delete_all_backtests() -> bool:
    """Delete all backtest results"""
```

### Simulation Engine

```python
# GET /api/v1/simulation/status
async def get_simulation_status() -> SimulationStatus:
    """Get simulation engine status"""

# POST /api/v1/simulation/start
async def start_simulation() -> SimulationStatus:
    """Start simulation engine"""

# POST /api/v1/simulation/stop
async def stop_simulation() -> SimulationStatus:
    """Stop simulation engine"""

# POST /api/v1/simulation/reset
async def reset_simulation() -> SimulationStatus:
    """Reset simulation to initial state"""

# GET /api/v1/simulation/portfolio
async def get_portfolio() -> Portfolio:
    """Get current portfolio"""

# GET /api/v1/simulation/positions
async def get_positions() -> List[Position]:
    """Get open positions"""

# GET /api/v1/simulation/trades
async def get_trades() -> List[Trade]:
    """Get trade history"""

# GET /api/v1/simulation/performance
async def get_performance() -> PerformanceMetrics:
    """Get performance metrics"""
```

### System Status

```python
# GET /api/v1/status/health
async def get_health() -> HealthStatus:
    """Get basic health status"""

# GET /api/v1/status/health/detailed
async def get_detailed_health() -> DetailedHealthStatus:
    """Get detailed health status"""

# GET /api/v1/status/metrics
async def get_metrics() -> SystemMetrics:
    """Get system metrics"""

# GET /api/v1/status/logs
async def get_logs(
    level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[LogEntry]:
    """Get system logs"""
```

## 🔧 Configuration

### API Configuration

```python
from src.api.config import APIConfig

config = APIConfig(
    host="0.0.0.0",
    port=8000,
    debug=False,
    reload=True,
    workers=1,
    log_level="INFO"
)
```

### Security Configuration

```python
from src.api.config import SecurityConfig

security_config = SecurityConfig(
    jwt_secret_key="your_secret_key",
    jwt_algorithm="HS256",
    access_token_expire_minutes=30,
    refresh_token_expire_days=7,
    password_min_length=8,
    max_login_attempts=5
)
```

### Rate Limiting Configuration

```python
from src.api.config import RateLimitConfig

rate_limit_config = RateLimitConfig(
    requests_per_minute=100,
    burst_size=20,
    window_size=60,
    enable_redis=False,
    redis_url="redis://localhost:6379"
)
```

## 🚨 Error Handling

### HTTP Status Codes

```python
# Success responses
200: OK - Request successful
201: Created - Resource created successfully
204: No Content - Request successful, no content to return

# Client errors
400: Bad Request - Invalid request parameters
401: Unauthorized - Authentication required
403: Forbidden - Access denied
404: Not Found - Resource not found
409: Conflict - Resource conflict
422: Unprocessable Entity - Validation error
429: Too Many Requests - Rate limit exceeded

# Server errors
500: Internal Server Error - Server error
502: Bad Gateway - Upstream service error
503: Service Unavailable - Service temporarily unavailable
```

### Error Response Format

```python
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input parameters",
        "details": [
            {
                "field": "symbol",
                "message": "Field is required"
            }
        ],
        "timestamp": "2024-01-15T10:30:00Z",
        "request_id": "req_123456789"
    }
}
```

### Custom Exceptions

```python
from src.api.exceptions import APIException

class ValidationError(APIException):
    """Validation error exception"""
    status_code = 422
    error_code = "VALIDATION_ERROR"

class ResourceNotFoundError(APIException):
    """Resource not found exception"""
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"

class RateLimitExceededError(APIException):
    """Rate limit exceeded exception"""
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
```

## 📊 WebSocket & SSE

### WebSocket Endpoints

```python
# WebSocket connection for real-time data
@app.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """WebSocket endpoint for real-time market data"""
    await websocket.accept()
    
    try:
        while True:
            # Send market data updates
            data = await get_market_data()
            await websocket.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
```

### Server-Sent Events

```python
# SSE endpoint for real-time notifications
@app.get("/api/v1/notifications/stream")
async def stream_notifications() -> EventSourceResponse:
    """Stream notifications via Server-Sent Events"""
    
    async def event_generator():
        while True:
            # Check for new notifications
            notifications = await get_new_notifications()
            
            for notification in notifications:
                yield {
                    "event": "notification",
                    "data": notification.json()
                }
            
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_generator())
```

## 🔒 Security

### Authentication

```python
from src.api.auth import get_current_user, create_access_token

# JWT token creation
access_token = create_access_token(
    data={"sub": user.email, "scopes": user.scopes}
)

# Protected endpoint
@router.get("/protected/")
async def protected_endpoint(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Protected endpoint requiring authentication"""
    return {"message": f"Hello {current_user.email}"}
```

### Rate Limiting

```python
from src.api.rate_limit import rate_limit

# Apply rate limiting to endpoint
@router.get("/api/v1/pairs/")
@rate_limit(max_requests=100, window_seconds=60)
async def get_pairs() -> List[Pair]:
    """Get all trading pairs with rate limiting"""
    return await pairs_service.get_all()
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Monitoring

### Health Checks

```python
from src.api.monitoring import HealthChecker

health_checker = HealthChecker()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return await health_checker.check_health()
```

### Metrics Collection

```python
from src.api.metrics import MetricsCollector

metrics = MetricsCollector()

@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    """Collect request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    metrics.record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    return response
```

### Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Structured logging
logger.info("API request processed",
           method=request.method,
           path=request.url.path,
           status_code=response.status_code,
           duration=duration,
           user_id=user_id)
```

## 🧪 Testing

### API Tests

```bash
# Run API tests
pytest tests/test_api/ -v

# Run specific test file
pytest tests/test_api/test_pairs.py -v

# Run with coverage
pytest tests/test_api/ --cov=src.api
```

### Integration Tests

```bash
# Run integration tests
pytest tests/test_api/ -m integration

# Test with live services
pytest tests/test_api/ --env=live
```

### API Client Testing

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_get_pairs():
    """Test getting all pairs"""
    response = client.get("/api/v1/pairs/")
    assert response.status_code == 200
    
    pairs = response.json()
    assert isinstance(pairs, list)
    assert len(pairs) > 0
```

## 🔧 Development

### Adding New Endpoints

1. Create router module in `src/api/routers/`
2. Define Pydantic schemas in `src/api/schemas/`
3. Implement business logic in services
4. Add tests in `tests/test_api/`
5. Update API documentation

### Custom Middleware

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Pre-processing
        logger.info(f"Request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        # Post-processing
        logger.info(f"Response: {response.status_code}")
        
        return response

app.add_middleware(CustomMiddleware)
```

### Environment-Specific Configuration

```python
from src.api.config import get_settings

settings = get_settings()

if settings.environment == "development":
    app.debug = True
    app.reload = True
elif settings.environment == "production":
    app.debug = False
    app.reload = False
```

## 🤝 Contributing

### Adding New Features

1. Create feature branch from main
2. Implement new functionality
3. Add comprehensive tests
4. Update API documentation
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

*Remember: Always validate API inputs and handle errors gracefully in production environments.*
