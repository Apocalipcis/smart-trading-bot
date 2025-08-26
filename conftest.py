"""
Pytest configuration and fixtures for the trading bot tests.

This file sets up the Python path and provides common test fixtures.
Note: This project now uses pyproject.toml for configuration instead of setup.py
"""

import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import common test dependencies
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Common test fixtures
@pytest.fixture
def mock_stream_manager():
    """Mock WebSocket stream manager for testing."""
    manager = Mock()
    manager.add_handler = Mock()
    manager.get_status = Mock(return_value=Mock(value='connected'))
    return manager

@pytest.fixture
def sample_candle_data():
    """Sample OHLCV data for testing."""
    import pandas as pd
    import datetime
    
    dates = pd.date_range(
        start=datetime.datetime.now(datetime.timezone.utc) - pd.Timedelta(hours=24),
        periods=100,
        freq='1min'
    )
    
    data = pd.DataFrame({
        'open': [100.0 + i * 0.1 for i in range(100)],
        'high': [100.5 + i * 0.1 for i in range(100)],
        'low': [99.5 + i * 0.1 for i in range(100)],
        'close': [100.2 + i * 0.1 for i in range(100)],
        'volume': [1000 + i * 10 for i in range(100)],
        'open_time': [int(d.timestamp() * 1000) for d in dates],
        'close_time': [int((d + pd.Timedelta(minutes=1)).timestamp() * 1000) for d in dates],
        'quote_volume': [100000 + i * 1000 for i in range(100)],
        'trades': [50 + i for i in range(100)],
        'taker_buy_base': [500 + i * 5 for i in range(100)],
        'taker_buy_quote': [50000 + i * 500 for i in range(100)]
    }, index=dates)
    
    return data

@pytest.fixture
def mock_binance_client():
    """Mock Binance client for testing."""
    client = Mock()
    client.get_exchange_info = AsyncMock(return_value={
        'symbols': [
            {
                'symbol': 'BTCUSDT',
                'status': 'TRADING',
                'baseAsset': 'BTC',
                'quoteAsset': 'USDT',
                'pricePrecision': 2,
                'quantityPrecision': 3,
                'baseAssetPrecision': 8,
                'quotePrecision': 2,
                'filters': [
                    {
                        'filterType': 'PRICE_FILTER',
                        'tickSize': '0.01',
                        'minPrice': '0.01',
                        'maxPrice': '1000000'
                    },
                    {
                        'filterType': 'LOT_SIZE',
                        'stepSize': '0.001',
                        'minQty': '0.001',
                        'maxQty': '1000000'
                    },
                    {
                        'filterType': 'MIN_NOTIONAL',
                        'minNotional': '10.0'
                    }
                ]
            }
        ]
    })
    return client

@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI application for testing."""
    app = Mock()
    app.include_router = Mock()
    app.add_middleware = Mock()
    app.add_exception_handler = Mock()
    return app

@pytest.fixture
def sample_trading_pair():
    """Sample trading pair data for testing."""
    return {
        'symbol': 'BTCUSDT',
        'base_asset': 'BTC',
        'quote_asset': 'USDT',
        'status': 'TRADING',
        'price_precision': 2,
        'quantity_precision': 3
    }
