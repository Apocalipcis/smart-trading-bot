"""
Tests for python-binance integration modules.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from src.data.binance_client_new import BinanceClient, BinanceConfig, KlineData
from src.data.downloader_new import DataDownloader


class TestBinanceConfig:
    """Test BinanceConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BinanceConfig()
        assert config.api_key is None
        assert config.api_secret is None
        assert config.testnet is False
        assert config.tld == "com"
        assert config.timeout == 30
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = BinanceConfig(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True,
            tld="us",
            timeout=60
        )
        assert config.api_key == "test_key"
        assert config.api_secret == "test_secret"
        assert config.testnet is True
        assert config.tld == "us"
        assert config.timeout == 60


class TestKlineData:
    """Test KlineData model."""
    
    def test_kline_data_creation(self):
        """Test creating KlineData instance."""
        kline = KlineData(
            open_time=1640995200000,
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=100.0,
            close_time=1640995260000,
            quote_volume=5000000.0,
            trades=150,
            taker_buy_base=60.0,
            taker_buy_quote=3000000.0
        )
        
        assert kline.open_time == 1640995200000
        assert kline.open == 50000.0
        assert kline.high == 51000.0
        assert kline.low == 49000.0
        assert kline.close == 50500.0
        assert kline.volume == 100.0
        assert kline.close_time == 1640995260000
        assert kline.quote_volume == 5000000.0
        assert kline.trades == 150
        assert kline.taker_buy_base == 60.0
        assert kline.taker_buy_quote == 3000000.0


class TestBinanceClient:
    """Test BinanceClient class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return BinanceConfig()
    
    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return BinanceClient(config)
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager."""
        mock_async_client = AsyncMock()
        
        with patch('src.data.binance_client_new.AsyncClient.create', return_value=mock_async_client):
            async with client as ctx_client:
                assert ctx_client._client == mock_async_client
            
            # Check that client was closed
            mock_async_client.close_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_exchange_info(self, client):
        """Test getting exchange info."""
        mock_async_client = AsyncMock()
        mock_async_client.futures_exchange_info.return_value = {"symbols": [], "rateLimits": []}
        
        with patch('src.data.binance_client_new.AsyncClient.create', return_value=mock_async_client):
            async with client:
                result = await client.get_exchange_info()
                
                assert result == {"symbols": [], "rateLimits": []}
                mock_async_client.futures_exchange_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_klines(self, client):
        """Test getting klines data."""
        mock_async_client = AsyncMock()
        mock_klines = [
            [1640995200000, "50000.0", "51000.0", "49000.0", "50500.0", "100.0", 
             1640995260000, "5000000.0", 150, "60.0", "3000000.0"]
        ]
        mock_async_client.futures_klines.return_value = mock_klines
        
        with patch('src.data.binance_client_new.AsyncClient.create', return_value=mock_async_client):
            async with client:
                result = await client.get_klines("BTCUSDT", "1h", limit=100)
                
                assert len(result) == 1
                assert isinstance(result[0], KlineData)
                assert result[0].open == 50000.0
                assert result[0].close == 50500.0
    
    @pytest.mark.asyncio
    async def test_get_historical_klines(self, client):
        """Test getting historical klines."""
        mock_async_client = AsyncMock()
        mock_klines = [
            [1640995200000, "50000.0", "51000.0", "49000.0", "50500.0", "100.0", 
             1640995260000, "5000000.0", 150, "60.0", "3000000.0"]
        ]
        mock_async_client.get_historical_klines.return_value = mock_klines
        
        with patch('src.data.binance_client_new.AsyncClient.create', return_value=mock_async_client):
            async with client:
                result = await client.get_historical_klines(
                    "BTCUSDT", "1h", "1 week ago UTC", "now UTC"
                )
                
                assert len(result) == 1
                assert isinstance(result[0], KlineData)
                mock_async_client.get_historical_klines.assert_called_once_with(
                    symbol="BTCUSDT",
                    interval="1h",
                    start_str="1 week ago UTC",
                    end_str="now UTC",
                    limit=1000
                )
    
    @pytest.mark.asyncio
    async def test_get_symbol_price(self, client):
        """Test getting symbol price."""
        mock_async_client = AsyncMock()
        mock_price = {"symbol": "BTCUSDT", "price": "50000.00"}
        mock_async_client.futures_symbol_ticker.return_value = mock_price
        
        with patch('src.data.binance_client_new.AsyncClient.create', return_value=mock_async_client):
            async with client:
                result = await client.get_symbol_price("BTCUSDT")
                
                assert result == mock_price
                mock_async_client.futures_symbol_ticker.assert_called_once_with(symbol="BTCUSDT")
    
    @pytest.mark.asyncio
    async def test_ping(self, client):
        """Test ping functionality."""
        mock_async_client = AsyncMock()
        mock_async_client.futures_ping.return_value = {}
        
        with patch('src.data.binance_client_new.AsyncClient.create', return_value=mock_async_client):
            async with client:
                result = await client.ping()
                
                assert result is True
                mock_async_client.futures_ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ping_failure(self, client):
        """Test ping failure handling."""
        mock_async_client = AsyncMock()
        mock_async_client.futures_ping.side_effect = Exception("Connection failed")
        
        with patch('src.data.binance_client_new.AsyncClient.create', return_value=mock_async_client):
            async with client:
                result = await client.ping()
                
                assert result is False


class TestDataDownloader:
    """Test DataDownloader class."""
    
    @pytest.fixture
    def downloader(self):
        """Create test downloader."""
        return DataDownloader(data_dir="./test_data")
    
    @pytest.fixture
    def mock_file_manager(self):
        """Create mock file manager."""
        mock_fm = MagicMock()
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_parent = MagicMock()
        mock_path.parent = mock_parent
        mock_fm.get_candle_path.return_value = mock_path
        return mock_fm
    
    @pytest.mark.asyncio
    async def test_download_symbol_data_new_file(self, downloader, mock_file_manager):
        """Test downloading data for a new symbol."""
        # Mock file manager
        downloader.file_manager = mock_file_manager
        
        # Mock BinanceClient
        mock_client = AsyncMock()
        mock_klines = [
            KlineData(
                open_time=1640995200000,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.0,
                close_time=1640995260000,
                quote_volume=5000000.0,
                trades=150,
                taker_buy_base=60.0,
                taker_buy_quote=3000000.0
            )
        ]
        mock_client.get_historical_klines.return_value = mock_klines
        
        # Mock file operations
        with patch('src.data.downloader_new.BinanceClient') as mock_client_class, \
             patch('src.data.downloader_new.BinanceConfig') as mock_config_class, \
             patch('pathlib.Path.mkdir'), \
             patch('pyarrow.parquet.write_table'):
            
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_config_class.return_value = MagicMock()
            
            result = await downloader.download_symbol_data(
                symbol="BTCUSDT",
                timeframe="1h",
                start_date=datetime.now(timezone.utc) - timedelta(days=7),
                end_date=datetime.now(timezone.utc),
                force_update=False
            )
            
            assert result["symbol"] == "BTCUSDT"
            assert result["timeframe"] == "1h"
            assert result["status"] == "downloaded"
    
    @pytest.mark.asyncio
    async def test_download_symbol_data_existing_file(self, downloader, mock_file_manager):
        """Test downloading data when file already exists."""
        # Mock file manager to return existing file
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_file_manager.get_candle_path.return_value = mock_path
        
        # Mock file stats
        mock_path.stat.return_value.st_size = 1024 * 1024  # 1MB
        
        # Mock parquet reading
        mock_table = MagicMock()
        mock_df = MagicMock()
        mock_df.__len__.return_value = 100
        mock_df.datetime.min.return_value = datetime.now(timezone.utc) - timedelta(days=7)
        mock_df.datetime.max.return_value = datetime.now(timezone.utc)
        mock_table.to_pandas.return_value = mock_df
        
        # Mock the file manager to return existing file
        downloader.file_manager = mock_file_manager
        
        with patch('pyarrow.parquet.read_table', return_value=mock_table):
            result = await downloader.download_symbol_data(
                symbol="BTCUSDT",
                timeframe="1h",
                start_date=datetime.now(timezone.utc) - timedelta(days=7),
                end_date=datetime.now(timezone.utc),
                force_update=False
            )
            
            assert result["status"] == "existing"
            assert result["total_candles"] == 100
    
    @pytest.mark.asyncio
    async def test_download_exotic_symbol_data(self, downloader):
        """Test downloading exotic symbol data."""
        # Mock BinanceClient to fail
        mock_client = AsyncMock()
        mock_client.get_historical_klines.side_effect = Exception("Symbol not found")
        
        with patch('src.data.downloader_new.BinanceClient') as mock_client_class, \
             patch('src.data.downloader_new.BinanceConfig') as mock_config_class:
            
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_config_class.return_value = MagicMock()
            
            with pytest.raises(NotImplementedError) as exc_info:
                await downloader.download_exotic_symbol_data(
                    symbol="BTC",
                    timeframe="15m",
                    start_date=datetime.now(timezone.utc) - timedelta(days=7),
                    end_date=datetime.now(timezone.utc)
                )
            
            assert "not yet implemented" in str(exc_info.value)
            assert "BTC" in str(exc_info.value)
    
    def test_validate_candle_data_valid(self, downloader):
        """Test candle data validation with valid data."""
        import pandas as pd
        
        # Create valid DataFrame
        df = pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=5, freq='1H', tz='UTC'),
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [95, 96, 97, 98, 99],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        # Should not raise any exception
        downloader._validate_candle_data(df, "BTCUSDT", "1h")
    
    def test_validate_candle_data_invalid_prices(self, downloader):
        """Test candle data validation with invalid prices."""
        import pandas as pd
        
        # Create DataFrame with invalid prices
        df = pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=3, freq='1H', tz='UTC'),
            'open': [100, 0, 102],  # 0 is invalid
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [101, 102, 103],
            'volume': [1000, 1100, 1200]
        })
        
        with pytest.raises(ValueError, match="Invalid prices"):
            downloader._validate_candle_data(df, "BTCUSDT", "1h")
    
    def test_validate_candle_data_invalid_ohlc(self, downloader):
        """Test candle data validation with invalid OHLC."""
        import pandas as pd
        
        # Create DataFrame with high < low
        df = pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=3, freq='1H', tz='UTC'),
            'open': [100, 101, 102],
            'high': [105, 96, 107],  # 96 < 97 (low)
            'low': [95, 97, 98],
            'close': [101, 102, 103],
            'volume': [1000, 1100, 1200]
        })
        
        with pytest.raises(ValueError, match="high < low"):
            downloader._validate_candle_data(df, "BTCUSDT", "1h")


if __name__ == "__main__":
    pytest.main([__file__])