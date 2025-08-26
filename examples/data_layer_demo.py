#!/usr/bin/env python3
"""
Demonstration of the data layer components.
"""
import asyncio
import logging
import os
from pathlib import Path

from src.data.binance_client import BinanceClient, BinanceConfig
from src.data.validators import BinanceValidator
from src.data.rate_limit import RateLimiter, RateLimitConfig, RequestType
from src.data.stream import WebSocketStreamManager, StreamConfig
from src.data.feed import BinanceDataFeed


async def demo_binance_client():
    """Demonstrate Binance client functionality."""
    print("=== Binance Client Demo ===")
    
    config = BinanceConfig(
        rest_url="https://fapi.binance.com",
        ws_url="wss://fstream.binance.com"
    )
    
    async with BinanceClient(config) as client:
        try:
            # Get exchange info
            print("Getting exchange info...")
            exchange_info = await client.get_exchange_info()
            print(f"Found {len(exchange_info.get('symbols', []))} symbols")
            
            # Get recent klines for BTCUSDT
            print("Getting recent klines for BTCUSDT...")
            klines = await client.get_klines("BTCUSDT", "1m", limit=5)
            print(f"Retrieved {len(klines)} klines")
            
            if klines:
                latest = klines[-1]
                print(f"Latest BTCUSDT price: ${latest.close}")
            
            # Get book ticker
            print("Getting book ticker...")
            ticker = await client.get_book_ticker("BTCUSDT")
            print(f"Bid: ${ticker.bid_price}, Ask: ${ticker.ask_price}")
            
        except Exception as e:
            print(f"Error: {e}")


def demo_validators():
    """Demonstrate validator functionality."""
    print("\n=== Validators Demo ===")
    
    validator = BinanceValidator()
    
    # Mock exchange info for BTCUSDT
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
    
    validator.set_symbol_info('BTCUSDT', exchange_info)
    
    # Test validations
    test_cases = [
        (50000.00, 1.000, "Valid order"),
        (50000.005, 1.000, "Invalid tick size"),
        (50000.00, 0.0005, "Below min notional"),
        (50000.00, 1.0005, "Invalid step size")
    ]
    
    for price, qty, description in test_cases:
        valid, msg = validator.validate_order('BTCUSDT', price, qty)
        status = "✓" if valid else "✗"
        print(f"{status} {description}: {msg}")
    
    # Test normalization
    print(f"\nPrice normalization examples:")
    print(f"50000.005 -> {validator.normalize_price('BTCUSDT', 50000.005)}")
    print(f"50000.009 -> {validator.normalize_price('BTCUSDT', 50000.009)}")


async def demo_rate_limiter():
    """Demonstrate rate limiter functionality."""
    print("\n=== Rate Limiter Demo ===")
    
    config = RateLimitConfig(
        requests_per_second=2,
        burst_size=3,
        retry_attempts=2,
        base_delay=0.1
    )
    
    rate_limiter = RateLimiter(config)
    await rate_limiter.start()
    
    async def test_function(name: str):
        print(f"Executing {name}")
        return f"Result from {name}"
    
    try:
        # Test rate limiting
        print("Testing rate limiting...")
        start_time = asyncio.get_event_loop().time()
        
        results = []
        for i in range(5):
            result = await rate_limiter.execute_with_retry(
                lambda: test_function(f"task_{i}"), 
                RequestType.REST, 
                f"task_{i}"
            )
            results.append(result)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        print(f"Executed {len(results)} tasks in {elapsed:.2f} seconds")
        print(f"Results: {results}")
        
    finally:
        await rate_limiter.stop()


def demo_data_feed():
    """Demonstrate data feed functionality."""
    print("\n=== Data Feed Demo ===")
    
    # Test feed initialization
    try:
        feed = BinanceDataFeed(
            symbol='BTCUSDT',
            interval='1m',
            data_dir='/data',
            live=False
        )
        
        print(f"Feed initialized: {feed.symbol} {feed.interval}")
        print(f"Mode: {'Live' if feed.live_mode else 'Offline'}")
        print(f"Data directory: {feed.data_dir}")
        
        # Test interval mapping
        interval = feed._get_expected_interval()
        print(f"Expected interval: {interval}")
        
    except Exception as e:
        print(f"Feed initialization error: {e}")


async def main():
    """Main demonstration function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Data Layer Components Demonstration")
    print("=" * 50)
    
    # Run demonstrations
    await demo_binance_client()
    demo_validators()
    await demo_rate_limiter()
    demo_data_feed()
    
    print("\n" + "=" * 50)
    print("Demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
