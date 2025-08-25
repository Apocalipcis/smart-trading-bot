# Trading Bot Infrastructure

This document describes the infrastructure setup for the Smart Trading Bot, including Docker configuration, deployment procedures, and monitoring.

## Architecture Overview

The trading bot is designed as a containerized application with the following components:

- **Backend API**: FastAPI application with structured logging
- **Database**: SQLite with WAL mode for performance
- **Data Storage**: Local file system with Parquet format
- **Monitoring**: Health checks and structured logging
- **CI/CD**: GitHub Actions pipeline

## Docker Setup

### Production Dockerfile

The application uses a multi-stage Dockerfile for optimized production builds:

```dockerfile
# Builder stage
FROM python:3.11-slim as builder
# ... build dependencies and virtual environment

# Production stage  
FROM python:3.11-slim as production
# ... runtime dependencies and application
```

**Key Features:**
- Multi-stage build for smaller final image
- Non-root user for security
- Health check endpoint
- Optimized layer caching

### Docker Compose

The application includes two Docker Compose configurations:

#### Production (`docker-compose.yml`)
```yaml
services:
  trading-bot:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    environment:
      - DATA_DIR=/data
      - DB_PATH=/data/app.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/status/health"]
```

#### Development (`docker-compose.dev.yml`)
```yaml
services:
  trading-bot-dev:
    build:
      target: builder
    volumes:
      - ./src:/app/src  # Live code reload
      - ./tests:/app/tests
    environment:
      - DEBUG_MODE=true
      - RELOAD=true
    command: ["uvicorn", "src.api.main:app", "--reload"]
```

## Deployment

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd smart-trading-bot
   cp config.example.env .env
   # Edit .env with your configuration
   ```

2. **Deploy with script:**
   ```bash
   ./scripts/deploy.sh deploy
   ```

3. **Manual deployment:**
   ```bash
   # Build image
   docker build -t smart-trading-bot .
   
   # Start services
   docker-compose up -d
   
   # Check health
   curl http://localhost:8000/api/v1/status/health
   ```

### Deployment Script

The `scripts/deploy.sh` script provides comprehensive deployment management:

```bash
# Full deployment (build, test, start)
./scripts/deploy.sh deploy

# Individual commands
./scripts/deploy.sh build    # Build Docker image
./scripts/deploy.sh test     # Run tests
./scripts/deploy.sh start    # Start services
./scripts/deploy.sh stop     # Stop services
./scripts/deploy.sh status   # Show status
./scripts/deploy.sh logs     # Show logs
./scripts/deploy.sh health   # Health check
./scripts/deploy.sh cleanup  # Clean up resources
```

## Configuration

### Environment Variables

Key configuration variables in `.env`:

```env
# Trading Configuration
TRADING_ENABLED=false
ORDER_CONFIRMATION_REQUIRED=true
MAX_OPEN_POSITIONS=5
MAX_RISK_PER_TRADE=2.0
MIN_RISK_REWARD_RATIO=3.0

# Exchange Configuration
EXCHANGE=binance_futures
WS_URL=wss://fstream.binance.com/ws
REST_URL=https://fapi.binance.com

# API Keys (for live trading)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# System Configuration
DATA_DIR=/data
DB_PATH=/data/app.db
LOG_LEVEL=INFO
DEBUG_MODE=false

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLED=false
```

### Data Directory Structure

```
/data/
├── app.db                 # SQLite database
├── candles/              # Historical candle data
│   └── binance_futures/
│       └── BTCUSDT/
│           └── 1m.parquet
├── backtests/            # Backtest results
│   └── 2024-01-15/
│       └── BTCUSDT_smc_1m.json
├── artifacts/            # Charts and reports
├── reports/              # Generated reports
└── logs/                 # Application logs
```

## Monitoring & Health Checks

### Health Endpoints

- **Basic Health**: `GET /api/v1/status/health`
- **Detailed Health**: `GET /api/v1/status/health/detailed`
- **Metrics**: `GET /api/v1/status/metrics`
- **System Info**: `GET /api/v1/status/info`

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": 3600.5,
  "database_connected": true,
  "exchange_connected": true
}
```

### Structured Logging

The application uses structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "src.api.routers.signals",
  "message": "Trading signal generated",
  "correlation_id": "req-123",
  "service": "smart-trading-bot",
  "version": "1.0.0",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "confidence": 0.85
}
```

## CI/CD Pipeline

### GitHub Actions

The CI/CD pipeline includes:

1. **Linting**: Ruff and Black formatting checks
2. **Type Checking**: MyPy static analysis
3. **Testing**: Pytest with coverage reporting
4. **Security**: Bandit and Safety scans
5. **Build**: Docker image building
6. **Deploy**: Staging and production deployments

### Pipeline Stages

```yaml
jobs:
  lint:          # Code quality checks
  type-check:    # Static type analysis
  test:          # Unit and integration tests
  security:      # Security vulnerability scans
  build:         # Docker image build
  deploy-staging: # Deploy to staging
  deploy-production: # Deploy to production
```

## Development

### Local Development

1. **Setup development environment:**
   ```bash
   # Install dependencies
   pip install -e .[dev]
   
   # Run tests
   pytest tests/
   
   # Start development server
   uvicorn src.api.main:app --reload
   ```

2. **Docker development:**
   ```bash
   # Start development container
   docker-compose -f docker-compose.dev.yml up
   
   # Access logs
   docker-compose -f docker-compose.dev.yml logs -f
   ```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test categories
pytest -m "unit" tests/
pytest -m "integration" tests/
pytest -m "slow" tests/
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check `DB_PATH` environment variable
   - Ensure data directory has write permissions
   - Verify SQLite file is not corrupted

2. **Exchange Connection Issues**
   - Verify API keys are correct
   - Check network connectivity
   - Ensure exchange endpoints are accessible

3. **Docker Build Failures**
   - Clear Docker cache: `docker system prune`
   - Check Dockerfile syntax
   - Verify all dependencies are available

4. **Health Check Failures**
   - Check application logs: `docker-compose logs`
   - Verify all required services are running
   - Check environment configuration

### Log Analysis

```bash
# View application logs
docker-compose logs -f trading-bot

# Filter logs by level
docker-compose logs | grep "ERROR"

# Search for specific patterns
docker-compose logs | grep "correlation_id"
```

### Performance Monitoring

```bash
# Check resource usage
docker stats

# Monitor API performance
curl -w "@curl-format.txt" http://localhost:8000/api/v1/status/health

# Check database performance
docker exec -it smart-trading-bot sqlite3 /data/app.db "PRAGMA stats;"
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Network Security**: Use HTTPS in production
3. **Container Security**: Run as non-root user
4. **Data Protection**: Encrypt sensitive data at rest
5. **Access Control**: Implement proper authentication/authorization

## Production Deployment

### Recommended Production Setup

1. **Reverse Proxy**: Use Nginx or Traefik
2. **SSL/TLS**: Configure HTTPS certificates
3. **Monitoring**: Integrate with Prometheus/Grafana
4. **Logging**: Centralized log aggregation
5. **Backup**: Regular database and data backups
6. **Scaling**: Consider horizontal scaling for high load

### Environment-Specific Configurations

```bash
# Production
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=WARNING
TRADING_ENABLED=true

# Staging
ENVIRONMENT=staging
DEBUG_MODE=false
LOG_LEVEL=INFO
TRADING_ENABLED=false

# Development
ENVIRONMENT=development
DEBUG_MODE=true
LOG_LEVEL=DEBUG
TRADING_ENABLED=false
```

## Support

For infrastructure issues:

1. Check the logs: `docker-compose logs`
2. Review this documentation
3. Check GitHub Issues
4. Contact the development team

## Changelog

### v1.0.0
- Initial infrastructure setup
- Docker containerization
- CI/CD pipeline
- Health monitoring
- Structured logging
