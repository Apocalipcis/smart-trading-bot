"""
Tests for the data layer components.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.data.validators import BinanceValidator, SymbolInfo
from src.data.rate_limit import RateLimiter, RateLimitConfig, RequestType
from src.data.feed import BinanceDataFeed


class TestBinanceValidator:
    """Test Binance exchange validations."""
    
    def test_symbol_info_creation(self):
        """Test SymbolInfo creation from exchange info."""
        exchange_info = {
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
        
        validator = BinanceValidator()
        validator.set_symbol_info('BTCUSDT', exchange_info)
        
        symbol_info = validator.get_symbol_info('BTCUSDT')
        assert symbol_info is not None
        assert symbol_info.symbol == 'BTCUSDT'
        assert symbol_info.tick_size == 0.01
        assert symbol_info.step_size == 0.001
        assert symbol_info.min_notional == 10.0
    
    def test_price_validation(self):
        """Test price validation logic."""
        validator = BinanceValidator()
        
        # Mock symbol info
        symbol_info = SymbolInfo(
            symbol='BTCUSDT',
            status='TRADING',
            base_asset='BTC',
            quote_asset='USDT',
            price_precision=2,
            quantity_precision=3,
            base_asset_precision=8,
            quote_precision=2,
            min_notional=10.0,
            tick_size=0.01,
            step_size=0.001,
            min_qty=0.001,
            max_qty=1000000,
            min_price=0.01,
            max_price=1000000
        )
        
        validator._symbol_info['BTCUSDT'] = symbol_info
        
        # Valid price
        valid, msg = validator.validate_price('BTCUSDT', 50000.00)
        assert valid
        assert "Price valid" in msg
        
        # Invalid tick size
        valid, msg = validator.validate_price('BTCUSDT', 50000.005)
        assert not valid
        assert "not aligned with tick size" in msg
        
        # Below minimum
        valid, msg = validator.validate_price('BTCUSDT', 0.005)
        assert not valid
        assert "below minimum" in msg
    
    def test_quantity_validation(self):
        """Test quantity validation logic."""
        validator = BinanceValidator()
        
        # Mock symbol info
        symbol_info = SymbolInfo(
            symbol='BTCUSDT',
            status='TRADING',
            base_asset='BTC',
            quote_asset='USDT',
            price_precision=2,
            quantity_precision=3,
            base_asset_precision=8,
            quote_precision=2,
            min_notional=10.0,
            tick_size=0.01,
            step_size=0.001,
            min_qty=0.001,
            max_qty=1000000,
            min_price=0.01,
            max_price=1000000
        )
        
        validator._symbol_info['BTCUSDT'] = symbol_info
        
        # Valid quantity
        valid, msg = validator.validate_quantity('BTCUSDT', 1.000)
        assert valid
        
        # Invalid step size
        valid, msg = validator.validate_quantity('BTCUSDT', 1.0005)
        assert not valid
        assert "not aligned with step size" in msg
    
    def test_notional_validation(self):
        """Test notional value validation."""
        validator = BinanceValidator()
        
        # Mock symbol info
        symbol_info = SymbolInfo(
            symbol='BTCUSDT',
            status='TRADING',
            base_asset='BTC',
            quote_asset='USDT',
            price_precision=2,
            quantity_precision=3,
            base_asset_precision=8,
            quote_precision=2,
            min_notional=10.0,
            tick_size=0.01,
            step_size=0.001,
            min_qty=0.001,
            max_qty=1000000,
            min_price=0.01,
            max_price=1000000
        )
        
        validator._symbol_info['BTCUSDT'] = symbol_info
        
        # Valid notional
        valid, msg = validator.validate_notional('BTCUSDT', 50000.00, 1.000)
        assert valid
        
        # Below minimum notional
        valid, msg = validator.validate_notional('BTCUSDT', 50000.00, 0.0001)
        assert not valid
        assert "below minimum" in msg
    
    def test_price_normalization(self):
        """Test price normalization to valid tick size."""
        validator = BinanceValidator()
        
        # Mock symbol info
        symbol_info = SymbolInfo(
            symbol='BTCUSDT',
            status='TRADING',
            base_asset='BTC',
            quote_asset='USDT',
            price_precision=2,
            quantity_precision=3,
            base_asset_precision=8,
            quote_precision=2,
            min_notional=10.0,
            tick_size=0.01,
            step_size=0.001,
            min_qty=0.001,
            max_qty=1000000,
            min_price=0.01,
            max_price=1000000
        )
        
        validator._symbol_info['BTCUSDT'] = symbol_info
        
        # Test normalization
        normalized = validator.normalize_price('BTCUSDT', 50000.005)
        assert normalized == 50000.00
        
        normalized = validator.normalize_price('BTCUSDT', 50000.009)
        assert normalized == 50000.01


class TestRateLimiter:
    """Test rate limiting and retry logic."""
    
    @pytest.mark.asyncio
    async def test_token_bucket_rate_limiting(self):
        """Test token bucket rate limiting."""
        config = RateLimitConfig(
            requests_per_second=2,
            burst_size=5,
            retry_attempts=2
        )
        
        rate_limiter = RateLimiter(config)
        await rate_limiter.start()
        
        # Test rate limiting
        start_time = asyncio.get_event_loop().time()
        
        # Should execute immediately (within burst capacity)
        for i in range(5):
            await rate_limiter.execute_with_retry(
                lambda: asyncio.sleep(0.1),
                RequestType.REST
            )
        
        # Next request should be rate limited
        await rate_limiter.execute_with_retry(
            lambda: asyncio.sleep(0.1),
            RequestType.REST
        )
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should take at least 0.5 seconds due to rate limiting
        assert elapsed >= 0.5
        
        await rate_limiter.stop()
    
    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic with exponential backoff."""
        config = RateLimitConfig(
            requests_per_second=10,
            burst_size=20,
            retry_attempts=3,
            base_delay=0.1
        )
        
        rate_limiter = RateLimiter(config)
        await rate_limiter.start()
        
        # Mock function that fails twice then succeeds
        call_count = 0
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated failure")
            return "success"
        
        # Should succeed after retries
        result = await rate_limiter.execute_with_retry(
            failing_function,
            RequestType.REST
        )
        
        assert result == "success"
        assert call_count == 3
        
        await rate_limiter.stop()
    
    @pytest.mark.asyncio
    async def test_idempotency(self):
        """Test idempotency key handling."""
        config = RateLimitConfig()
        rate_limiter = RateLimiter(config)
        await rate_limiter.start()
        
        # Mock function
        async def test_function():
            return {"result": "success", "timestamp": asyncio.get_event_loop().time()}
        
        # First call
        result1 = await rate_limiter.execute_with_retry(
            test_function,
            RequestType.REST,
            idempotency_key="test_key_1"
        )
        
        # Second call with same key should return cached result
        result2 = await rate_limiter.execute_with_retry(
            test_function,
            RequestType.REST,
            idempotency_key="test_key_1"
        )
        
        # Results should be identical
        assert result1 == result2
        
        await rate_limiter.stop()


class TestBinanceDataFeed:
    """Test Backtrader data feed."""
    
    def test_feed_initialization(self):
        """Test feed initialization with parameters."""
        feed = BinanceDataFeed(
            symbol='BTCUSDT',
            interval='1m',
            data_dir='/data',
            live=False
        )
        
        assert feed.symbol == 'BTCUSDT'
        assert feed.interval == '1m'
        assert feed.data_dir == '/data'
        assert not feed.live_mode
    
    def test_offline_mode_setup(self):
        """Test offline mode setup (without actual file)."""
        with patch('pathlib.Path.exists', return_value=False):
            feed = BinanceDataFeed(
                symbol='BTCUSDT',
                interval='1m',
                data_dir='/data',
                live=False
            )
            
            # Should raise FileNotFoundError when file doesn't exist
            with pytest.raises(FileNotFoundError):
                feed._setup_offline_mode()
    
    def test_live_mode_setup(self):
        """Test live mode setup."""
        mock_stream_manager = Mock()
        
        feed = BinanceDataFeed(
            symbol='BTCUSDT',
            interval='1m',
            data_dir='/data',
            live=True,
            stream_manager=mock_stream_manager
        )
        
        assert feed.live_mode
        assert feed.stream_manager == mock_stream_manager
    
    def test_interval_mapping(self):
        """Test timeframe to timedelta mapping."""
        feed = BinanceDataFeed(symbol='BTCUSDT', interval='5m')
        
        expected_interval = feed._get_expected_interval()
        assert expected_interval.total_seconds() == 300  # 5 minutes
        
        feed = BinanceDataFeed(symbol='BTCUSDT', interval='1h')
        expected_interval = feed._get_expected_interval()
        assert expected_interval.total_seconds() == 3600  # 1 hour


if __name__ == "__main__":
    pytest.main([__file__])
