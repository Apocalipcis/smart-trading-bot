#!/usr/bin/env python3
"""
Historical Data Download Demo using python-binance

This script demonstrates how to download historical candle data
from Binance using the python-binance library.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.data.downloader_new import DataDownloader


async def demo_single_download():
    """Demonstrate downloading data for a single symbol/timeframe."""
    print("=== Single Symbol Download Demo (python-binance) ===")
    
    # Create downloader
    downloader = DataDownloader(data_dir="./data")
    
    # Download BTCUSDT 1h data for the last 7 days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    try:
        result = await downloader.download_symbol_data(
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            force_update=False
        )
        
        print(f"✅ Download successful!")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Timeframe: {result['timeframe']}")
        print(f"   Candles: {result['total_candles']}")
        print(f"   File size: {result['file_size_mb']:.2f} MB")
        print(f"   Date range: {result['start_date']} to {result['end_date']}")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")


async def demo_multiple_downloads():
    """Demonstrate downloading data for multiple symbols and timeframes."""
    print("\n=== Multiple Downloads Demo (python-binance) ===")
    
    # Create downloader
    downloader = DataDownloader(data_dir="./data")
    
    # Define symbols and timeframes
    symbols = ["BTCUSDT", "ETHUSDT"]
    timeframes = ["1h", "4h"]
    
    # Download last 30 days of data
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    try:
        results = await downloader.download_multiple_symbols(
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            force_update=False
        )
        
        print(f"✅ Downloaded {len(results)} datasets:")
        for result in results:
            if "error" in result:
                print(f"   ❌ {result['symbol']} {result['timeframe']}: {result['error']}")
            else:
                print(f"   ✅ {result['symbol']} {result['timeframe']}: {result['total_candles']} candles")
        
    except Exception as e:
        print(f"❌ Downloads failed: {e}")


async def demo_data_inventory():
    """Demonstrate checking available data."""
    print("\n=== Data Inventory Demo (python-binance) ===")
    
    # Create downloader
    downloader = DataDownloader(data_dir="./data")
    
    try:
        inventory = await downloader.get_available_data()
        
        print(f"📊 Data Inventory:")
        print(f"   Exchange: {inventory['exchange']}")
        print(f"   Directory: {inventory['data_directory']}")
        print(f"   Total symbols: {inventory['total_symbols']}")
        
        if 'data' in inventory and inventory['data']:
            print(f"   Available data:")
            for symbol, timeframes in inventory['data'].items():
                print(f"     {symbol}: {list(timeframes.keys())}")
        else:
            print(f"   No data found")
        
    except Exception as e:
        print(f"❌ Inventory check failed: {e}")


async def demo_exotic_symbol():
    """Demonstrate attempting to download exotic symbol data."""
    print("\n=== Exotic Symbol Demo (python-binance) ===")
    
    # Create downloader
    downloader = DataDownloader(data_dir="./data")
    
    # Try to download data for an exotic symbol
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    try:
        result = await downloader.download_exotic_symbol_data(
            symbol="BTC",  # This is an exotic symbol
            timeframe="15m",
            start_date=start_date,
            end_date=end_date,
            force_update=False
        )
        
        print(f"✅ Exotic symbol download successful!")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Timeframe: {result['timeframe']}")
        print(f"   Candles: {result['total_candles']}")
        
    except NotImplementedError as e:
        print(f"ℹ️  Exotic symbol not yet implemented: {e}")
        print(f"   This demonstrates the need for Binance Vision API integration")
    except Exception as e:
        print(f"❌ Exotic symbol download failed: {e}")


async def demo_python_binance_features():
    """Demonstrate python-binance specific features."""
    print("\n=== Python-Binance Features Demo ===")
    
    try:
        from src.data.binance_client_new import BinanceClient, BinanceConfig
        
        # Create client
        config = BinanceConfig()
        async with BinanceClient(config) as client:
            
            # Test connectivity
            print("🔌 Testing connectivity...")
            if await client.ping():
                print("   ✅ Connected to Binance API")
            else:
                print("   ❌ Connection failed")
            
            # Get server time
            print("🕐 Getting server time...")
            time_info = await client.get_server_time()
            server_time = datetime.fromtimestamp(time_info['serverTime'] / 1000, tz=timezone.utc)
            print(f"   Server time: {server_time}")
            
            # Get exchange info
            print("📊 Getting exchange info...")
            exchange_info = await client.get_exchange_info()
            print(f"   Total symbols: {len(exchange_info['symbols'])}")
            print(f"   Rate limits: {len(exchange_info['rateLimits'])}")
            
            # Get current prices
            print("💰 Getting current prices...")
            btc_price = await client.get_symbol_price("BTCUSDT")
            eth_price = await client.get_symbol_price("ETHUSDT")
            print(f"   BTCUSDT: ${float(btc_price['price']):,.2f}")
            print(f"   ETHUSDT: ${float(eth_price['price']):,.2f}")
            
    except Exception as e:
        print(f"❌ Python-binance features demo failed: {e}")


async def main():
    """Run all demos."""
    print("🚀 Python-Binance Integration Demo")
    print("=" * 50)
    
    # Run demos
    await demo_single_download()
    await demo_multiple_downloads()
    await demo_data_inventory()
    await demo_exotic_symbol()
    await demo_python_binance_features()
    
    print("\n" + "=" * 50)
    print("✅ Demo completed!")
    print("\nKey benefits of python-binance:")
    print("   • Simplified API calls")
    print("   • Built-in rate limiting")
    print("   • Better error handling")
    print("   • Support for historical data")
    print("   • Futures API support")
    print("   • WebSocket capabilities")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demo
    asyncio.run(main())
