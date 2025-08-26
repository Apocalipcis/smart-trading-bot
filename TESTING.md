# Testing Documentation

## Overview

This document outlines the testing strategy, procedures, and guidelines for the Smart Trading Bot to ensure code quality, reliability, and performance.

## Testing Strategy

### Testing Pyramid

The testing approach follows the testing pyramid model:

1. **Unit Tests** (70%): Fast, isolated tests for individual components
2. **Integration Tests** (20%): Tests for component interactions
3. **End-to-End Tests** (10%): Full system workflow tests

### Test Categories

- **Unit Tests**: Individual functions and classes
- **Integration Tests**: API endpoints and database operations
- **Performance Tests**: Load testing and benchmarking
- **Security Tests**: Vulnerability scanning and penetration testing
- **Simulation Tests**: Trading simulation validation

## Test Setup

### Environment Configuration

Create a test environment configuration:

```bash
# test.env
TESTING_MODE=true
TEST_DATABASE_PATH=./test_data/test.db
TEST_DATA_DIR=./test_data
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

### Test Dependencies

Install test dependencies:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Or install specific test packages
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Test Database Setup

```python
# conftest.py
import pytest
import tempfile
import os
from src.storage.db import init_db

@pytest.fixture
def test_db():
    """Create temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Initialize test database
    init_db(db_path)
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_simulation.py

# Run specific test function
pytest tests/test_simulation.py::test_simulation_engine_initialization
```

### Test Categories

```bash
# Run unit tests only
pytest -m "unit"

# Run integration tests only
pytest -m "integration"

# Run slow tests
pytest -m "slow"

# Skip slow tests
pytest -m "not slow"

# Run asyncio tests
pytest -m "asyncio"
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Generate XML coverage report (for CI/CD)
pytest --cov=src --cov-report=xml

# Generate terminal coverage report
pytest --cov=src --cov-report=term-missing
```

## Unit Testing

### Test Structure

```python
# tests/test_simulation.py
import pytest
from decimal import Decimal
from src.simulation.engine import SimulationEngine
from src.simulation.config import SimulationConfig

class TestSimulationEngine:
    """Test simulation engine functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SimulationConfig(
            initial_capital=Decimal("10000.0"),
            commission=Decimal("0.001")
        )
    
    @pytest.fixture
    def engine(self, config):
        """Create test simulation engine."""
        return SimulationEngine(config)
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert engine.config.initial_capital == Decimal("10000.0")
        assert engine.config.commission == Decimal("0.001")
    
    def test_portfolio_creation(self, engine):
        """Test portfolio creation."""
        portfolio = engine.get_portfolio()
        assert portfolio.total_value == Decimal("10000.0")
        assert portfolio.cash == Decimal("10000.0")
        assert portfolio.positions_value == Decimal("0.0")
    
    @pytest.mark.asyncio
    async def test_order_submission(self, engine):
        """Test order submission."""
        from src.orders.types import Order, OrderSide, OrderType
        
        order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        result = await engine.submit_order(order)
        assert result.success is True
        assert result.order_id is not None
```

### Mocking External Dependencies

```python
# tests/test_data_layer.py
import pytest
from unittest.mock import Mock, patch
from src.data.binance_client import BinanceClient

class TestBinanceClient:
    """Test Binance client functionality."""
    
    @pytest.fixture
    def mock_response(self):
        """Mock API response."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "symbol": "BTCUSDT",
            "price": "45000.50"
        }
        return response
    
    @patch('httpx.AsyncClient.get')
    async def test_get_price(self, mock_get, mock_response):
        """Test price retrieval."""
        mock_get.return_value = mock_response
        
        client = BinanceClient()
        price = await client.get_price("BTCUSDT")
        
        assert price == "45000.50"
        mock_get.assert_called_once()
```

### Test Data Management

```python
# tests/conftest.py
import pytest
import pandas as pd
from datetime import datetime, timezone

@pytest.fixture
def sample_candle_data():
    """Create sample candle data for testing."""
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='1min', tz=timezone.utc),
        'open': [45000.0] * 100,
        'high': [45100.0] * 100,
        'low': [44900.0] * 100,
        'close': [45050.0] * 100,
        'volume': [100.0] * 100
    })

@pytest.fixture
def sample_trading_signals():
    """Create sample trading signals for testing."""
    return [
        {
            'side': 'long',
            'entry': 45000.0,
            'stop_loss': 44000.0,
            'take_profit': 47000.0,
            'confidence': 0.8,
            'timestamp': datetime.now(timezone.utc)
        }
    ]
```

## Integration Testing

### API Endpoint Testing

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/status/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_simulation_status(self):
        """Test simulation status endpoint."""
        response = client.get("/api/v1/simulation/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "mode" in data
        assert "portfolio_value" in data
    
    def test_create_backtest(self):
        """Test backtest creation endpoint."""
        backtest_data = {
            "pair": "BTCUSDT",
            "strategy": "SMC",
            "timeframe": "1m",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-15T00:00:00Z",
            "initial_capital": 10000.0
        }
        
        response = client.post("/api/v1/backtests", json=backtest_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["status"] == "running"
```

### Database Integration Testing

```python
# tests/test_storage.py
import pytest
from src.storage.db import get_db_manager
from src.storage.simulation import SimulationStorage

class TestDatabaseOperations:
    """Test database operations."""
    
    @pytest.mark.asyncio
    async def test_simulation_storage(self, test_db):
        """Test simulation data storage."""
        storage = SimulationStorage(test_db)
        
        # Test portfolio storage
        portfolio_data = {
            "total_value": 10000.0,
            "cash": 10000.0,
            "positions_value": 0.0,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        await storage.save_portfolio_snapshot(portfolio_data)
        
        # Test portfolio retrieval
        snapshots = await storage.get_portfolio_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0]["total_value"] == 10000.0
    
    @pytest.mark.asyncio
    async def test_order_storage(self, test_db):
        """Test order storage operations."""
        storage = SimulationStorage(test_db)
        
        order_data = {
            "id": "SIM-123",
            "pair": "BTCUSDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.001,
            "status": "filled"
        }
        
        await storage.save_order(order_data)
        
        orders = await storage.get_orders()
        assert len(orders) == 1
        assert orders[0]["id"] == "SIM-123"
```

## Performance Testing

### Load Testing

```python
# tests/test_performance.py
import pytest
import asyncio
import time
from src.simulation.engine import SimulationEngine

class TestPerformance:
    """Test system performance."""
    
    @pytest.mark.slow
    def test_simulation_engine_performance(self):
        """Test simulation engine performance."""
        config = SimulationConfig(initial_capital=10000.0)
        engine = SimulationEngine(config)
        
        start_time = time.time()
        
        # Simulate 1000 price updates
        for i in range(1000):
            engine.update_price("BTCUSDT", 45000.0 + i, 45001.0 + i, 45000.5 + i)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within 1 second
        assert duration < 1.0
        print(f"1000 price updates completed in {duration:.3f} seconds")
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_order_processing(self):
        """Test concurrent order processing."""
        config = SimulationConfig(initial_capital=10000.0)
        engine = SimulationEngine(config)
        
        from src.orders.types import Order, OrderSide, OrderType
        
        # Create 100 concurrent orders
        orders = []
        for i in range(100):
            order = Order(
                pair="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("0.001")
            )
            orders.append(order)
        
        start_time = time.time()
        
        # Submit orders concurrently
        tasks = [engine.submit_order(order) for order in orders]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within 5 seconds
        assert duration < 5.0
        assert all(result.success for result in results)
        print(f"100 concurrent orders processed in {duration:.3f} seconds")
```

### Memory Usage Testing

```python
# tests/test_memory.py
import pytest
import psutil
import os
from src.simulation.engine import SimulationEngine

class TestMemoryUsage:
    """Test memory usage patterns."""
    
    @pytest.mark.slow
    def test_memory_usage_growth(self):
        """Test memory usage growth over time."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        config = SimulationConfig(initial_capital=10000.0)
        engine = SimulationEngine(config)
        
        # Simulate extended operation
        for i in range(10000):
            engine.update_price("BTCUSDT", 45000.0 + i, 45001.0 + i, 45000.5 + i)
            
            if i % 1000 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"Memory usage at iteration {i}: {current_memory:.2f} MB")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be less than 100MB
        assert memory_growth < 100.0
        print(f"Total memory growth: {memory_growth:.2f} MB")
```

## Security Testing

### Input Validation Testing

```python
# tests/test_security.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestSecurity:
    """Test security measures."""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        # Attempt SQL injection in pair parameter
        malicious_pair = "BTCUSDT'; DROP TABLE orders; --"
        
        response = client.get(f"/api/v1/signals?pair={malicious_pair}")
        
        # Should not crash and should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_xss_prevention(self):
        """Test XSS prevention."""
        # Attempt XSS in message parameter
        malicious_message = "<script>alert('xss')</script>"
        
        response = client.post("/api/v1/notifications/test", json={
            "message": malicious_message
        })
        
        # Should handle malicious input safely
        assert response.status_code in [200, 400, 422]
    
    def test_rate_limiting(self):
        """Test rate limiting."""
        # Make many requests quickly
        for i in range(150):
            response = client.get("/api/v1/status/health")
            
            if response.status_code == 429:
                # Rate limit hit
                break
        
        # Should eventually hit rate limit
        assert response.status_code == 429
```

## Simulation Testing

### Trading Logic Validation

```python
# tests/test_trading_logic.py
import pytest
from decimal import Decimal
from src.simulation.engine import SimulationEngine
from src.orders.types import Order, OrderSide, OrderType

class TestTradingLogic:
    """Test trading logic and calculations."""
    
    @pytest.fixture
    def engine(self):
        """Create test engine."""
        config = SimulationConfig(
            initial_capital=Decimal("10000.0"),
            commission=Decimal("0.001"),
            slippage=Decimal("0.0001")
        )
        return SimulationEngine(config)
    
    @pytest.mark.asyncio
    async def test_position_sizing(self, engine):
        """Test position sizing calculations."""
        # Submit order with 2% risk
        order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        result = await engine.submit_order(order)
        assert result.success
        
        # Check position sizing
        portfolio = engine.get_portfolio()
        position = portfolio.get_position("BTCUSDT")
        
        # Position should be properly sized
        assert position is not None
        assert position.quantity == Decimal("0.001")
    
    @pytest.mark.asyncio
    async def test_pnl_calculation(self, engine):
        """Test P&L calculation accuracy."""
        # Submit buy order
        buy_order = Order(
            pair="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001")
        )
        
        await engine.submit_order(buy_order)
        
        # Update price to simulate profit
        engine.update_price("BTCUSDT", 46000.0, 46001.0, 46000.5)
        
        portfolio = engine.get_portfolio()
        position = portfolio.get_position("BTCUSDT")
        
        # Calculate expected P&L
        entry_price = 45000.0  # Approximate entry
        current_price = 46000.5
        quantity = 0.001
        expected_pnl = (current_price - entry_price) * quantity
        
        assert abs(position.unrealized_pnl - expected_pnl) < 1.0
```

## Continuous Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
        args: [--fix]
  
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Test Coverage Requirements

### Coverage Targets

- **Overall Coverage**: ≥80%
- **Critical Components**: ≥90%
- **API Endpoints**: ≥95%
- **Trading Logic**: ≥95%

### Coverage Exclusions

```python
# .coveragerc
[run]
source = src
omit = 
    */tests/*
    */__init__.py
    */migrations/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## Test Data Management

### Synthetic Data Generation

```python
# tests/utils/data_generator.py
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

def generate_candle_data(symbol: str, periods: int = 1000, start_date: datetime = None):
    """Generate synthetic candle data for testing."""
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=periods)
    
    timestamps = pd.date_range(start_date, periods=periods, freq='1min', tz=timezone.utc)
    
    # Generate realistic price data
    base_price = 45000.0
    price_changes = np.random.normal(0, 100, periods)
    prices = base_price + np.cumsum(price_changes)
    
    data = []
    for i, timestamp in enumerate(timestamps):
        price = prices[i]
        data.append({
            'timestamp': timestamp,
            'open': price,
            'high': price + abs(np.random.normal(0, 50)),
            'low': price - abs(np.random.normal(0, 50)),
            'close': price + np.random.normal(0, 20),
            'volume': np.random.uniform(50, 200)
        })
    
    return pd.DataFrame(data)

def generate_trading_signals(count: int = 10):
    """Generate synthetic trading signals for testing."""
    signals = []
    base_price = 45000.0
    
    for i in range(count):
        price = base_price + np.random.normal(0, 1000)
        signal = {
            'side': np.random.choice(['long', 'short']),
            'entry': price,
            'stop_loss': price * (0.98 if np.random.choice([True, False]) else 1.02),
            'take_profit': price * (1.05 if np.random.choice([True, False]) else 0.95),
            'confidence': np.random.uniform(0.5, 1.0),
            'timestamp': datetime.now(timezone.utc) - timedelta(minutes=i)
        }
        signals.append(signal)
    
    return signals
```

## Best Practices

### Test Organization

1. **Test File Naming**: `test_<module_name>.py`
2. **Test Class Naming**: `Test<ClassName>`
3. **Test Method Naming**: `test_<functionality>`
4. **Fixture Organization**: Group related fixtures in conftest.py

### Test Quality

1. **Test Independence**: Each test should be independent
2. **Test Isolation**: Use fixtures for setup/teardown
3. **Test Clarity**: Clear test names and assertions
4. **Test Coverage**: Test both success and failure cases

### Performance Considerations

1. **Fast Tests**: Unit tests should run quickly
2. **Resource Management**: Clean up resources after tests
3. **Mocking**: Mock external dependencies for speed
4. **Parallel Execution**: Use pytest-xdist for parallel testing

## Troubleshooting

### Common Test Issues

```bash
# Database locked errors
rm -f test_data/test.db

# Import errors
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Async test issues
pytest --asyncio-mode=auto

# Coverage issues
pytest --cov=src --cov-report=term-missing
```

### Debug Test Failures

```python
# Add debug prints
def test_debug_example():
    print("Debug: Starting test")
    result = some_function()
    print(f"Debug: Result = {result}")
    assert result is not None
```

## Changelog

### v1.0.0
- Initial testing documentation
- Unit testing guidelines
- Integration testing procedures
- Performance testing framework
- Security testing measures
- CI/CD integration
- Test coverage requirements
- Best practices and troubleshooting
